import axios from "axios";

const http = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || "/api/v1",
  timeout: 30000,
  headers: { "Content-Type": "application/json" },
});

http.interceptors.request.use((config) => {
  const token = localStorage.getItem("autoheal_token");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

http.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem("autoheal_token");
      localStorage.removeItem("autoheal_user");
      if (window.location.pathname !== "/login") window.location.href = "/login";
    }
    const message = error.response?.data?.message || "请求失败，请稍后重试";
    return Promise.reject(new Error(message));
  },
);

export default http;
