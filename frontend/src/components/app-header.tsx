"use client";

import { useEffect, useState } from "react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { AppBreadcrumbs } from "@/components/app-breadcrumbs";
import { CustomSidebarTrigger } from "@/components/custom-sidebar-trigger";
import { navLinks } from "@/components/app-shared";
import { NavUser } from "@/components/nav-user";
import { SendIcon, BellIcon } from "lucide-react";

const activeItem = navLinks.find((item) => item.isActive);

const NOTIFICATION_COUNT = 3;

export function AppHeader() {
	const [badgeOpen, setBadgeOpen] = useState(false);

	useEffect(() => {
		const t = setTimeout(() => setBadgeOpen(true), 600);
		return () => clearTimeout(t);
	}, []);

	return (
		<header
			className={cn(
				"sticky top-0 z-50 flex h-14 shrink-0 items-center justify-between gap-2 border-b px-4 md:px-6"
			)}
		>
			<div className="flex items-center gap-3">
				<CustomSidebarTrigger />
				<Separator
					className="mr-2 h-4 data-[orientation=vertical]:self-center"
					orientation="vertical"
				/>
				<AppBreadcrumbs page={activeItem} />
			</div>
			<div className="flex items-center gap-3">
				<Button size="icon" variant="outline">
					<SendIcon />
				</Button>
				<Button
					aria-label="Notifications"
					className="relative"
					size="icon"
					variant="outline"
				>
					<BellIcon />
					<span className="t-badge" data-open={badgeOpen ? "true" : "false"}>
						<span className="t-badge-dot flex h-4 min-w-4 items-center justify-center rounded-full bg-primary px-1 text-[9px] font-bold text-white leading-none">
							{NOTIFICATION_COUNT}
						</span>
					</span>
				</Button>
				<Separator
					className="h-4 data-[orientation=vertical]:self-center"
					orientation="vertical"
				/>
				<NavUser />
			</div>
		</header>
	);
}
