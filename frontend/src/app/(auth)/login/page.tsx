"use client";

import { useState, useRef, useEffect } from "react";
import { useRouter } from "next/navigation";
import { Zap } from "lucide-react";
import { useAuthStore } from "@/store/auth-store";

export default function LoginPage() {
  const [pin, setPin] = useState(["", "", "", "", "", ""]);
  const [loading, setLoading] = useState(false);
  const [localError, setLocalError] = useState("");
  const inputs = useRef<(HTMLInputElement | null)[]>([]);
  const { pinLogin, error: storeError, clearError } = useAuthStore();
  const router = useRouter();

  const displayError = localError || storeError || "";

  useEffect(() => {
    inputs.current[0]?.focus();
  }, []);

  const handleChange = (index: number, value: string) => {
    if (!/^\d?$/.test(value)) return;
    const newPin = [...pin];
    newPin[index] = value;
    setPin(newPin);
    setLocalError("");
    clearError();
    if (value && index < 5) {
      inputs.current[index + 1]?.focus();
    }
    if (newPin.every((d) => d !== "")) {
      submitPin(newPin.join(""));
    }
  };

  const handleKeyDown = (index: number, e: React.KeyboardEvent) => {
    if (e.key === "Backspace" && !pin[index] && index > 0) {
      inputs.current[index - 1]?.focus();
    }
  };

  const submitPin = async (pinStr: string) => {
    setLoading(true);
    setLocalError("");
    try {
      await pinLogin(pinStr);
      router.replace("/dashboard");
    } catch {
      setLocalError("Invalid PIN");
      setPin(["", "", "", "", "", ""]);
      setTimeout(() => inputs.current[0]?.focus(), 50);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex h-screen w-screen items-center justify-center bg-cortex-bg grid-bg">
      <div className="flex flex-col items-center gap-8">
        <div className="flex flex-col items-center gap-3">
          <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-cortex-accent shadow-lg shadow-cortex-accent/20">
            <Zap className="h-6 w-6 text-white" />
          </div>
          <div className="text-center">
            <h1 className="text-2xl font-bold text-cortex-text tracking-tight">CortexOS</h1>
            <p className="text-cortex-muted mt-1 text-sm">Enter PIN to continue</p>
          </div>
        </div>

        <div className="rounded-xl border border-cortex-border bg-cortex-surface p-8 shadow-2xl flex flex-col items-center gap-6">
          <div className="flex gap-3">
            {pin.map((digit, i) => (
              <input
                key={i}
                ref={(el) => { inputs.current[i] = el; }}
                type="password"
                inputMode="numeric"
                maxLength={1}
                value={digit}
                onChange={(e) => handleChange(i, e.target.value)}
                onKeyDown={(e) => handleKeyDown(i, e)}
                disabled={loading}
                className="w-12 h-14 text-center text-2xl font-mono rounded-lg bg-cortex-bg border border-cortex-border text-cortex-text focus:outline-none focus:border-cortex-accent focus:ring-1 focus:ring-cortex-accent disabled:opacity-50 caret-transparent transition-colors"
              />
            ))}
          </div>

          {displayError && (
            <p className="text-cortex-error text-sm">{displayError}</p>
          )}
          {loading && (
            <p className="text-cortex-muted text-sm">Verifying...</p>
          )}
        </div>

        <p className="text-center text-xs text-cortex-muted">
          CortexOS Australia · Secure Access
        </p>
      </div>
    </div>
  );
}
