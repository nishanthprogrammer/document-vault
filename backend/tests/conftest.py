import os
from collections.abc import Generator

import boto3
import fakeredis
import pytest
from fastapi.testclient import TestClient
from moto import mock_aws
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

os.environ.setdefault("DATABASE_URL", "sqlite://")
os.environ.setdefault("JWT_SECRET", "test-secret-key-for-pytest")
os.environ.setdefault("AWS_ACCESS_KEY_ID", "testing")
os.environ.setdefault("AWS_SECRET_ACCESS_KEY", "testing")
os.environ.setdefault("AWS_DEFAULT_REGION", "us-east-1")
os.environ.setdefault("S3_BUCKET", "documents")
os.environ.setdefault("S3_ENDPOINT", "")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")

from app.config import get_settings  # noqa: E402
from app.database import Base, get_db  # noqa: E402
import app.database as db_module  # noqa: E402
from app.main import app  # noqa: E402
from app.redis_client import reset_redis_client, set_redis_client  # noqa: E402

get_settings.cache_clear()


def _create_engine():
    settings = get_settings()
    if settings.database_url.startswith("sqlite"):
        return create_engine(
            settings.database_url,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
    return create_engine(settings.database_url, pool_pre_ping=True)


@pytest.fixture()
def client() -> Generator[TestClient, None, None]:
    get_settings.cache_clear()

    engine = _create_engine()
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    db_module.engine = engine
    db_module.SessionLocal = TestingSessionLocal
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    fake_redis = fakeredis.FakeRedis(decode_responses=True)
    set_redis_client(fake_redis)

    def override_get_db() -> Generator[Session, None, None]:
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    with mock_aws():
        settings = get_settings()
        s3 = boto3.client("s3", region_name="us-east-1")
        s3.create_bucket(Bucket=settings.s3_bucket)

        app.dependency_overrides[get_db] = override_get_db
        with TestClient(app) as test_client:
            yield test_client
        app.dependency_overrides.clear()

    Base.metadata.drop_all(bind=engine)
    reset_redis_client()
    get_settings.cache_clear()


@pytest.fixture()
def auth_headers(client: TestClient) -> dict[str, str]:
    email = "user@example.com"
    password = "securepass123"
    client.post("/api/v1/auth/register", json={"email": email, "password": password})
    login = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    token = login.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
