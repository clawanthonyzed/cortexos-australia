import type { ReactNode } from "react";
import {
  LayoutDashboardIcon,
  BotIcon,
  ListChecksIcon,
  WorkflowIcon,
  BrainIcon,
  BarChart3Icon,
  DollarSignIcon,
  ShoppingBagIcon,
  NetworkIcon,
  SettingsIcon,
  HelpCircleIcon,
  ActivityIcon,
  KeyIcon,
} from "lucide-react";

export type SidebarNavItem = {
  title: string;
  path?: string;
  icon?: ReactNode;
  isActive?: boolean;
  subItems?: SidebarNavItem[];
};

export type SidebarNavGroup = {
  label?: string;
  items: SidebarNavItem[];
};

export const navGroups: SidebarNavGroup[] = [
  {
    items: [
      {
        title: "Dashboard",
        path: "/dashboard",
        icon: <LayoutDashboardIcon />,
        isActive: true,
      },
    ],
  },
  {
    label: "Operations",
    items: [
      {
        title: "Agents",
        path: "/agents",
        icon: <BotIcon />,
      },
      {
        title: "Tasks",
        path: "/tasks",
        icon: <ListChecksIcon />,
      },
      {
        title: "Workflows",
        path: "/workflows",
        icon: <WorkflowIcon />,
      },
      {
        title: "Memory",
        path: "/memory",
        icon: <BrainIcon />,
      },
    ],
  },
  {
    label: "Intelligence",
    items: [
      {
        title: "Knowledge Graph",
        path: "/knowledge-graph",
        icon: <NetworkIcon />,
      },
      {
        title: "Analytics",
        path: "/logs",
        icon: <BarChart3Icon />,
      },
    ],
  },
  {
    label: "Commerce",
    items: [
      {
        title: "Products",
        path: "/products",
        icon: <ShoppingBagIcon />,
      },
      {
        title: "Finance",
        path: "/finance",
        icon: <DollarSignIcon />,
      },
    ],
  },
  {
    label: "System",
    items: [
      {
        title: "Settings",
        icon: <SettingsIcon />,
        subItems: [
          { title: "General", path: "/settings" },
          { title: "API Keys", path: "/settings/api-keys" },
          { title: "Team", path: "/settings/team" },
          { title: "Billing", path: "/settings/billing" },
        ],
      },
    ],
  },
];

export const footerNavLinks: SidebarNavItem[] = [
  {
    title: "Help",
    path: "/help",
    icon: <HelpCircleIcon />,
  },
  {
    title: "System Status",
    path: "/status",
    icon: <ActivityIcon />,
  },
];

export const navLinks: SidebarNavItem[] = [
  ...navGroups.flatMap((group) =>
    group.items.flatMap((item) =>
      item.subItems?.length ? [item, ...item.subItems] : [item]
    )
  ),
  ...footerNavLinks,
];
