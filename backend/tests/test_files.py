import io

from app.config import get_settings


def test_upload_creates_file_record(client, auth_headers):
    files = {"file": ("report.pdf", io.BytesIO(b"%PDF-1.4 test content"), "application/pdf")}
    response = client.post("/api/v1/files/upload", headers=auth_headers, files=files)
    assert response.status_code == 201
    data = response.json()
    assert data["filename"] == "report.pdf"
    assert data["mime_type"] == "application/pdf"
    assert data["size_bytes"] > 0


def test_list_returns_only_own_files(client, auth_headers):
    files = {"file": ("mine.pdf", io.BytesIO(b"%PDF-1.4 mine"), "application/pdf")}
    client.post("/api/v1/files/upload", headers=auth_headers, files=files)

    other = client.post(
        "/api/v1/auth/register",
        json={"email": "other@example.com", "password": "password123"},
    )
    assert other.status_code == 201
    other_login = client.post(
        "/api/v1/auth/login",
        json={"email": "other@example.com", "password": "password123"},
    )
    other_headers = {"Authorization": f"Bearer {other_login.json()['access_token']}"}

    response = client.get("/api/v1/files", headers=auth_headers)
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["filename"] == "mine.pdf"

    other_list = client.get("/api/v1/files", headers=other_headers)
    assert other_list.status_code == 200
    assert other_list.json() == []


def test_download_returns_presigned_url(client, auth_headers):
    files = {"file": ("doc.pdf", io.BytesIO(b"%PDF-1.4 doc"), "application/pdf")}
    upload = client.post("/api/v1/files/upload", headers=auth_headers, files=files)
    file_id = upload.json()["id"]

    response = client.get(f"/api/v1/files/{file_id}/download", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "url" in data
    assert data["expires_in"] == get_settings().presigned_url_expires_seconds


def test_download_other_users_file_returns_404(client, auth_headers):
    files = {"file": ("private.pdf", io.BytesIO(b"%PDF-1.4 private"), "application/pdf")}
    upload = client.post("/api/v1/files/upload", headers=auth_headers, files=files)
    file_id = upload.json()["id"]

    client.post("/api/v1/auth/register", json={"email": "intruder@example.com", "password": "password123"})
    intruder_login = client.post(
        "/api/v1/auth/login",
        json={"email": "intruder@example.com", "password": "password123"},
    )
    intruder_headers = {"Authorization": f"Bearer {intruder_login.json()['access_token']}"}

    response = client.get(f"/api/v1/files/{file_id}/download", headers=intruder_headers)
    assert response.status_code == 404


def test_delete_removes_file(client, auth_headers):
    files = {"file": ("delete-me.pdf", io.BytesIO(b"%PDF-1.4 delete"), "application/pdf")}
    upload = client.post("/api/v1/files/upload", headers=auth_headers, files=files)
    file_id = upload.json()["id"]

    delete = client.delete(f"/api/v1/files/{file_id}", headers=auth_headers)
    assert delete.status_code == 204

    listing = client.get("/api/v1/files", headers=auth_headers)
    assert listing.json() == []


def test_upload_over_size_limit_returns_413(client, auth_headers, monkeypatch):
    settings = get_settings()
    monkeypatch.setattr(settings, "max_upload_size_bytes", 10)

    large_content = b"x" * 20
    files = {"file": ("big.pdf", io.BytesIO(large_content), "application/pdf")}
    response = client.post("/api/v1/files/upload", headers=auth_headers, files=files)
    assert response.status_code == 413


def test_upload_over_rate_limit_returns_429(client, auth_headers, monkeypatch):
    settings = get_settings()
    monkeypatch.setattr(settings, "upload_rate_limit", 2)

    for i in range(2):
        files = {"file": (f"file{i}.pdf", io.BytesIO(b"%PDF-1.4"), "application/pdf")}
        response = client.post("/api/v1/files/upload", headers=auth_headers, files=files)
        assert response.status_code == 201

    files = {"file": ("one-too-many.pdf", io.BytesIO(b"%PDF-1.4"), "application/pdf")}
    response = client.post("/api/v1/files/upload", headers=auth_headers, files=files)
    assert response.status_code == 429
    assert response.headers.get("retry-after") == str(settings.upload_rate_window_seconds)
