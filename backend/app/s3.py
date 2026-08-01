from typing import BinaryIO

import boto3
from botocore.client import Config

from app.config import get_settings


def _client(endpoint_url: str | None = None):
    settings = get_settings()
    
    kwargs = {
    "service_name": "s3",
    "region_name": settings.aws_region,
    "aws_access_key_id": settings.aws_access_key_id,
    "aws_secret_access_key": settings.aws_secret_access_key,
    "config": Config(signature_version="s3v4"),
}
    url = endpoint_url if endpoint_url is not None else settings.s3_endpoint
    if url:
        kwargs["endpoint_url"] = url
    return boto3.client(**kwargs)


def upload_fileobj(fileobj: BinaryIO, key: str, content_type: str) -> None:
    settings = get_settings()
    client = _client()
    client.upload_fileobj(
        fileobj,
        settings.s3_bucket,
        key,
        ExtraArgs={"ContentType": content_type},
    )


def delete_object(key: str) -> None:
    settings = get_settings()
    client = _client()
    client.delete_object(Bucket=settings.s3_bucket, Key=key)


def generate_presigned_url(key: str, expires_in: int | None = None) -> str:
    settings = get_settings()
    public_endpoint = settings.s3_public_endpoint or settings.s3_endpoint
    client = _client(endpoint_url=public_endpoint)
    expiry = expires_in or settings.presigned_url_expires_seconds
    return client.generate_presigned_url(
        "get_object",
        Params={"Bucket": settings.s3_bucket, "Key": key},
        ExpiresIn=expiry,
    )
