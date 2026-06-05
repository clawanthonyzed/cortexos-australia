import type React from "react";

export const LogoIcon = (props: React.ComponentProps<"svg">) => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" {...props}>
    <polygon points="12 2 22 7 22 17 12 22 2 17 2 7" />
    <circle cx="12" cy="12" r="3" />
    <line x1="12" y1="9" x2="12" y2="2" />
    <line x1="12" y1="15" x2="12" y2="22" />
    <line x1="9" y1="10.5" x2="2" y2="7" />
    <line x1="15" y1="10.5" x2="22" y2="7" />
    <line x1="9" y1="13.5" x2="2" y2="17" />
    <line x1="15" y1="13.5" x2="22" y2="17" />
  </svg>
);

export const Logo = (props: React.ComponentProps<"svg">) => (
  <svg viewBox="0 0 100 24" fill="none" {...props}>
    <polygon points="12 2 22 7 22 17 12 22 2 17 2 7" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
    <circle cx="12" cy="12" r="3" stroke="currentColor" strokeWidth="1.5" />
    <text x="28" y="17" fontFamily="system-ui, sans-serif" fontWeight="600" fontSize="13" fill="currentColor">CortexOS</text>
  </svg>
);
