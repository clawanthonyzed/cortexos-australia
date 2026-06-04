"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Zap, Eye, EyeOff, AlertCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useAuthStore } from "@/store/auth-store";
import type { Metadata } from "next";

export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const { login, isLoading, error, clearError } = useAuthStore();
  const router = useRouter();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await login(email, password);
      router.replace("/dashboard");
    } catch {
      // error is set in store
    }
  };

  return (
    <div className="flex h-screen w-screen items-center justify-center bg-cortex-bg grid-bg">
      <div className="w-full max-w-sm">
        {/* Logo */}
        <div className="flex flex-col items-center mb-8">
          <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-cortex-accent mb-3 shadow-lg shadow-cortex-accent/20">
            <Zap className="h-6 w-6 text-white" />
          </div>
          <h1 className="text-xl font-bold text-cortex-text">CortexOS</h1>
          <p className="text-sm text-cortex-muted">Agentic Operating System</p>
        </div>

        {/* Card */}
        <div className="rounded-xl border border-cortex-border bg-cortex-surface p-6 shadow-2xl">
          <h2 className="text-base font-semibold text-cortex-text mb-1">Sign in</h2>
          <p className="text-sm text-cortex-muted mb-6">Enter your credentials to access the command center</p>

          {error && (
            <div className="flex items-center gap-2 rounded-md bg-cortex-error/10 border border-cortex-error/20 px-3 py-2 mb-4">
              <AlertCircle className="h-4 w-4 text-cortex-error flex-shrink-0" />
              <p className="text-sm text-cortex-error">{error}</p>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-1.5">
              <Label htmlFor="email">Email</Label>
              <Input
                id="email"
                type="email"
                placeholder="operator@cortexos.ai"
                value={email}
                onChange={(e) => { setEmail(e.target.value); clearError(); }}
                required
                autoComplete="email"
              />
            </div>

            <div className="space-y-1.5">
              <Label htmlFor="password">Password</Label>
              <div className="relative">
                <Input
                  id="password"
                  type={showPassword ? "text" : "password"}
                  placeholder="••••••••"
                  value={password}
                  onChange={(e) => { setPassword(e.target.value); clearError(); }}
                  required
                  autoComplete="current-password"
                  className="pr-10"
                />
                <button
                  type="button"
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-cortex-muted hover:text-cortex-text transition-colors"
                  onClick={() => setShowPassword(!showPassword)}
                  aria-label={showPassword ? "Hide password" : "Show password"}
                >
                  {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </button>
              </div>
            </div>

            <Button
              type="submit"
              className="w-full"
              disabled={isLoading || !email || !password}
              size="lg"
            >
              {isLoading ? "Signing in..." : "Sign in"}
            </Button>
          </form>

          {/* Dev bypass */}
          {process.env.NODE_ENV === "development" && (
            <div className="mt-4 pt-4 border-t border-cortex-border">
              <button
                type="button"
                onClick={() => router.replace("/dashboard")}
                className="w-full text-center text-xs text-cortex-muted hover:text-cortex-accent transition-colors"
              >
                Dev: Skip login → Dashboard
              </button>
            </div>
          )}
        </div>

        <p className="mt-4 text-center text-xs text-cortex-muted">
          CortexOS Australia · Secure Access
        </p>
      </div>
    </div>
  );
}
