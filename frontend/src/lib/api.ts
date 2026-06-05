import axios, {
  type AxiosInstance,
  type AxiosError,
  type InternalAxiosRequestConfig,
} from "axios";
import { getAccessToken, getRefreshToken, setTokens, clearTokens } from "./auth";

const BASE_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

let isRefreshing = false;
let failedQueue: Array<{
  resolve: (token: string) => void;
  reject: (error: unknown) => void;
}> = [];

function processQueue(error: unknown, token: string | null): void {
  failedQueue.forEach(({ resolve, reject }) => {
    if (error) {
      reject(error);
    } else if (token) {
      resolve(token);
    }
  });
  failedQueue = [];
}

export const api: AxiosInstance = axios.create({
  baseURL: BASE_URL,
  timeout: 30_000,
  headers: {
    "Content-Type": "application/json",
  },
});

// Request interceptor — attach JWT
api.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = getAccessToken();
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error: unknown) => Promise.reject(error)
);

// Response interceptor — handle 401 and auto-refresh
api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & {
      _retry?: boolean;
    };

    if (error.response?.status === 401 && !originalRequest._retry) {
      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject });
        }).then((token) => {
          if (originalRequest.headers) {
            originalRequest.headers.Authorization = `Bearer ${token}`;
          }
          return api(originalRequest);
        });
      }

      originalRequest._retry = true;
      isRefreshing = true;

      const refreshToken = getRefreshToken();
      if (!refreshToken) {
        clearTokens();
        if (typeof window !== "undefined") {
          window.location.href = "/login";
        }
        return Promise.reject(error);
      }

      try {
        const { data } = await axios.post<{
          access_token: string;
          refresh_token: string;
        }>(`${BASE_URL}/auth/refresh`, { refresh_token: refreshToken });

        setTokens(data.access_token, data.refresh_token);
        processQueue(null, data.access_token);

        if (originalRequest.headers) {
          originalRequest.headers.Authorization = `Bearer ${data.access_token}`;
        }
        return api(originalRequest);
      } catch (refreshError) {
        processQueue(refreshError, null);
        clearTokens();
        if (typeof window !== "undefined") {
          window.location.href = "/login";
        }
        return Promise.reject(refreshError);
      } finally {
        isRefreshing = false;
      }
    }

    return Promise.reject(error);
  }
);

// SWR-compatible fetcher
export async function fetcher<T>(url: string): Promise<T> {
  const { data } = await api.get<T>(url);
  return data;
}

// Typed API helpers
export const apiClient = {
  get: <T>(url: string, params?: Record<string, unknown>) =>
    api.get<T>(url, { params }).then((r) => r.data),

  post: <T>(url: string, body?: unknown) =>
    api.post<T>(url, body).then((r) => r.data),

  put: <T>(url: string, body?: unknown) =>
    api.put<T>(url, body).then((r) => r.data),

  patch: <T>(url: string, body?: unknown) =>
    api.patch<T>(url, body).then((r) => r.data),

  delete: <T>(url: string) => api.delete<T>(url).then((r) => r.data),
};
