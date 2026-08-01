import { ChangeEvent, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  clearToken,
  deleteFile,
  FileRecord,
  getDownloadUrl,
  getToken,
  listFiles,
  uploadFile,
} from "../api/client";

function formatBytes(bytes: number) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export default function Dashboard() {
  const navigate = useNavigate();
  const [files, setFiles] = useState<FileRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState("");

  async function loadFiles() {
    setLoading(true);
    setError("");
    try {
      const response = await listFiles();
      setFiles(response.data);
    } catch {
      setError("Failed to load files");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    if (!getToken()) {
      navigate("/login");
      return;
    }
    loadFiles();
  }, [navigate]);

  async function handleUpload(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    if (!file) return;
    setUploading(true);
    setError("");
    try {
      await uploadFile(file);
      await loadFiles();
    } catch (err: unknown) {
      const message =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ??
        "Upload failed";
      setError(String(message));
    } finally {
      setUploading(false);
      event.target.value = "";
    }
  }

  async function handleDownload(fileId: string) {
    try {
      const response = await getDownloadUrl(fileId);
      window.open(response.data.url, "_blank");
    } catch {
      setError("Failed to get download link");
    }
  }

  async function handleDelete(fileId: string, filename: string) {
    if (!window.confirm(`Delete "${filename}"?`)) return;
    try {
      await deleteFile(fileId);
      await loadFiles();
    } catch {
      setError("Failed to delete file");
    }
  }

  function handleLogout() {
    clearToken();
    navigate("/login");
  }

  return (
    <div className="container">
      <div className="card">
        <div className="header">
          <div>
            <h1>Document Vault</h1>
            <p>Your files</p>
          </div>
          <button className="secondary" onClick={handleLogout}>
            Logout
          </button>
        </div>

        <div className="upload-row">
          <input
            type="file"
            accept=".pdf,image/jpeg,image/png,image/webp"
            onChange={handleUpload}
            disabled={uploading}
          />
          {uploading && <span>Uploading...</span>}
        </div>

        {error && <p className="error">{error}</p>}

        {loading ? (
          <p className="empty">Loading files...</p>
        ) : files.length === 0 ? (
          <p className="empty">No files yet. Upload a PDF or image to get started.</p>
        ) : (
          <table>
            <thead>
              <tr>
                <th>Name</th>
                <th>Type</th>
                <th>Size</th>
                <th>Uploaded</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {files.map((file) => (
                <tr key={file.id}>
                  <td>{file.filename}</td>
                  <td>{file.mime_type}</td>
                  <td>{formatBytes(file.size_bytes)}</td>
                  <td>{new Date(file.created_at).toLocaleString()}</td>
                  <td className="actions">
                    <button onClick={() => handleDownload(file.id)}>Download</button>
                    <button className="danger" onClick={() => handleDelete(file.id, file.filename)}>
                      Delete
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
