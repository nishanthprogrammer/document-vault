import axios from "axios";

const TOKEN_KEY = "access_token";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL ?? "/api/v1",
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem(TOKEN_KEY);
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem(TOKEN_KEY);
      if (window.location.pathname !== "/login" && window.location.pathname !== "/register") {
        window.location.href = "/login";
      }
    }
    return Promise.reject(error);
  },
);

export function setToken(token: string) {
  localStorage.setItem(TOKEN_KEY, token);
}

export function clearToken() {
  localStorage.removeItem(TOKEN_KEY);
}

export function getToken() {
  return localStorage.getItem(TOKEN_KEY);
}

export interface FileRecord {
  id: string;
  filename: string;
  size_bytes: number;
  mime_type: string;
  created_at: string;
}

export async function register(email: string, password: string) {
  return api.post("/auth/register", { email, password });
}

export async function login(email: string, password: string) {
  return api.post<{ access_token: string; token_type: string }>("/auth/login", {
    email,
    password,
  });
}

export async function listFiles() {
  return api.get<FileRecord[]>("/files");
}

export async function uploadFile(file: File) {
  const formData = new FormData();
  formData.append("file", file);
  return api.post<FileRecord>("/files/upload", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
}

export async function getDownloadUrl(fileId: string) {
  return api.get<{ url: string; expires_in: number }>(`/files/${fileId}/download`);
}

export async function deleteFile(fileId: string) {
  return api.delete(`/files/${fileId}`);
}

export default api;
