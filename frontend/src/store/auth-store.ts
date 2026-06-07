import { create } from "zustand";
import { persist } from "zustand/middleware";
import {
  type AuthUser,
  setTokens,
  clearTokens,
  setStoredUser,
} from "@/lib/auth";
import { apiClient } from "@/lib/api";

interface LoginResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

interface AuthState {
  user: AuthUser | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  setUser: (user: AuthUser) => void;
  clearError: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,

      login: async (email: string, password: string) => {
        set({ isLoading: true, error: null });
        try {
          const tokens = await apiClient.post<LoginResponse>("/auth/login", {
            email,
            password,
          });
          setTokens(tokens.access_token, tokens.refresh_token);
          const user = await apiClient.get<AuthUser>("/auth/me");
          setStoredUser(user);
          set({ user, isAuthenticated: true, isLoading: false });
        } catch (err: unknown) {
          const message =
            err instanceof Error ? err.message : "Login failed. Check your credentials.";
          set({ error: message, isLoading: false });
          throw err;
        }
      },

      logout: () => {
        clearTokens();
        set({ user: null, isAuthenticated: false, error: null });
        if (typeof window !== "undefined") {
          window.location.href = "/login";
        }
      },

      setUser: (user: AuthUser) => {
        setStoredUser(user);
        set({ user, isAuthenticated: true });
      },

      clearError: () => set({ error: null }),
    }),
    {
      name: "cortexos-auth",
      partialize: (state) => ({
        user: state.user,
        isAuthenticated: state.isAuthenticated,
      }),
    }
  )
);
