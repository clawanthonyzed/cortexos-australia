import type { Metadata, Viewport } from "next";
import "./globals.css";
import { Toaster } from "sonner";

export const metadata: Metadata = {
  title: {
    default: "CortexOS",
    template: "%s | CortexOS",
  },
  description: "Agentic Operating System — Command Center for AI-driven ventures",
  icons: {
    icon: "/favicon.ico",
  },
};

export const viewport: Viewport = {
  themeColor: "#0a0a0b",
  colorScheme: "dark",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className="bg-cortex-bg text-cortex-text antialiased">
        {children}
        <Toaster
          theme="dark"
          position="bottom-right"
          toastOptions={{
            style: {
              background: "#111113",
              border: "1px solid #1e1e24",
              color: "#e4e4f0",
            },
          }}
        />
      </body>
    </html>
  );
}
