import axios from "axios";

export const apiClient = axios.create({
  baseURL: "/api",
  headers: {
    "Content-Type": "application/json",
  },
  withCredentials: true,
});

// Response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Skip redirect if already on the login page (avoids infinite reload loop)
      // or if the request was to /auth/me (AuthProvider handles that gracefully)
      const isLoginPage = window.location.pathname === "/login";
      const isAuthMeRequest = error.config?.url === "/auth/me";
      if (!isLoginPage && !isAuthMeRequest) {
        window.location.href = "/login";
      }
    }
    return Promise.reject(error);
  }
);

