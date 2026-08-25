"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  Search,
  ListChecks,
  Sparkles,
  Send,
  MessageSquare,
  Phone,
  Users,
  CheckSquare,
  Settings,
} from "lucide-react";

import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
} from "@/components/ui/sidebar";

const mainNav = [
  { title: "Dashboard", url: "/", icon: LayoutDashboard },
  { title: "Lead Discovery", url: "/leads", icon: Search },
  { title: "Qualification", url: "/qualification", icon: ListChecks },
  { title: "AI Analysis", url: "/analysis", icon: Sparkles },
  { title: "Outreach", url: "/outreach", icon: Send },
  { title: "Replies", url: "/replies", icon: MessageSquare },
  { title: "Calling Workspace", url: "/calling", icon: Phone },
  { title: "CRM", url: "/crm", icon: Users },
  { title: "Tasks", url: "/tasks", icon: CheckSquare },
];

const settingsNav = [{ title: "Settings", url: "/settings", icon: Settings }];

export function AppSidebar() {
  const pathname = usePathname();

  return (
    <Sidebar collapsible="icon" className="border-r">
      <SidebarHeader className="px-3 py-4">
        <div className="flex items-center gap-2.5 px-1">
          <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-primary text-sm font-bold text-primary-foreground shadow-sm">
            NC
          </div>
          <div className="flex flex-col leading-tight group-data-[collapsible=icon]:hidden">
            <span className="text-sm font-semibold">NexCraft Solutions</span>
            <span className="text-xs text-muted-foreground">
              AI Sales OS
            </span>
          </div>
        </div>
      </SidebarHeader>
      <SidebarContent className="gap-4 px-2">
        <SidebarGroup>
          <SidebarGroupLabel className="px-2 text-[11px] font-semibold tracking-wider text-sidebar-foreground/50 uppercase">
            Sales Pipeline
          </SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu className="gap-0.5">
              {mainNav.map((item) => (
                <SidebarMenuItem key={item.url}>
                  <SidebarMenuButton
                    render={<Link href={item.url} />}
                    isActive={pathname === item.url}
                    className="h-9"
                  >
                    <item.icon />
                    <span>{item.title}</span>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              ))}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
        <SidebarGroup>
          <SidebarGroupLabel className="px-2 text-[11px] font-semibold tracking-wider text-sidebar-foreground/50 uppercase">
            Settings
          </SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu className="gap-0.5">
              {settingsNav.map((item) => (
                <SidebarMenuItem key={item.url}>
                  <SidebarMenuButton
                    render={<Link href={item.url} />}
                    isActive={pathname === item.url}
                    className="h-9"
                  >
                    <item.icon />
                    <span>{item.title}</span>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              ))}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>
      <SidebarFooter className="px-3 py-3">
        <div className="flex items-center gap-2 rounded-md bg-sidebar-accent/50 px-2.5 py-2 group-data-[collapsible=icon]:hidden">
          <span className="h-1.5 w-1.5 shrink-0 rounded-full bg-emerald-500" />
          <span className="text-xs text-muted-foreground">
            Local development
          </span>
        </div>
      </SidebarFooter>
    </Sidebar>
  );
}
