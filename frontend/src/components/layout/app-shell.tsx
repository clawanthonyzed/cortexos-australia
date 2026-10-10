"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/store/auth-store";
import { useWebSocket } from "@/hooks/use-websocket";
import { SidebarInset, SidebarProvider } from "@/components/ui/sidebar";
import { AppHeader } from "@/components/app-header";
import { AppSidebar } from "@/components/app-sidebar";

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
  const [hydrated, setHydrated] = useState(false);

  useEffect(() => {
    if (useAuthStore.persist.hasHydrated()) {
      setHydrated(true);
    } else {
      const unsub = useAuthStore.persist.onFinishHydration(() => setHydrated(true));
      return unsub;
    }
  }, []);

  useEffect(() => {
    if (!hydrated) return;
    if (!isAuthenticated) {
      router.replace("/login");
    }
  }, [isAuthenticated, hydrated, router]);

  return (
    <div className="overflow-hidden">
      <WebSocketInitializer />
      <SidebarProvider className="relative h-svh">
        <AppSidebar />
        <SidebarInset className="md:peer-data-[variant=inset]:ml-0">
          <AppHeader />
          <div className="flex flex-1 flex-col gap-4 overflow-y-auto p-4 md:p-6">
            {children}
          </div>
        </SidebarInset>
      </SidebarProvider>
    </div>
  );
}
