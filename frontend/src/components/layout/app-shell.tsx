"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { Sidebar } from "./sidebar";
import { TopBar } from "./topbar";
import { useAuthStore } from "@/store/auth-store";
import { useWebSocket } from "@/hooks/use-websocket";

interface AppShellProps {
  children: React.ReactNode;
}

function WebSocketInitializer() {
  useWebSocket();
  return null;
}

export function AppShell({ children }: AppShellProps) {
  const { isAuthenticated } = useAuthStore();
  const router = useRouter();

  useEffect(() => {
    // In dev mode, skip auth gate to allow browsing
    if (process.env.NODE_ENV === "development") return;
    if (!isAuthenticated) {
      router.replace("/login");
    }
  }, [isAuthenticated, router]);

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-cortex-bg">
      <WebSocketInitializer />
      <Sidebar />
      <div className="flex flex-1 flex-col min-w-0 overflow-hidden">
        <TopBar />
        <main className="flex-1 overflow-y-auto overflow-x-hidden">
          <div className="mx-auto max-w-[1600px] p-6">
            {children}
          </div>
        </main>
      </div>
    </div>
  );
}
