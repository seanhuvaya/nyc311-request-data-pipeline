import {
    LayoutDashboard,
    Building2,
    TrendingUp,
    MapPin,
    Layers,
    Gauge,
    Phone,
    Grid3x3,
} from "lucide-react"
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
} from "@/components/ui/sidebar"
import {ModeToggle} from "@/components/mode-toggle"
import {Badge} from "@/components/ui/badge"
import type {NavPage} from "@/types"

const NAV_ITEMS: {
    id: NavPage
    label: string
    icon: React.ComponentType<{ className?: string }>
    badge?: string
}[] = [
    {id: "overview", label: "Executive Overview", icon: LayoutDashboard},
    // {id: "agency", label: "Agency Performance", icon: Building2},
    // {id: "complaints", label: "Complaint Trends", icon: TrendingUp},
    // {id: "geo", label: "Geographic View", icon: MapPin},
    // {id: "backlog", label: "Backlog & Operations", icon: Layers, badge: "Live"},
    // {id: "sla", label: "SLA Performance", icon: Gauge},
    // {id: "borough-heatmap", label: "Borough Heatmap", icon: Grid3x3},
]

interface AppSidebarProps {
    currentPage: NavPage
    onNavigate: (page: NavPage) => void
}

export function AppSidebar({currentPage, onNavigate}: AppSidebarProps) {
    return (
        <Sidebar collapsible="icon">
            <SidebarHeader>
                <SidebarMenu>
                    <SidebarMenuItem>
                        <SidebarMenuButton
                            size="lg"
                            className="pointer-events-none select-none"
                        >
                            <div
                                className="flex size-8 items-center justify-center rounded-lg bg-primary text-primary-foreground">
                                <Phone className="size-4"/>
                            </div>
                            <div className="flex flex-col gap-0.5 leading-none">
                                <span className="text-sm font-semibold">NYC 311</span>
                                <span className="text-xs text-muted-foreground">
                  Pipeline Dashboard
                </span>
                            </div>
                        </SidebarMenuButton>
                    </SidebarMenuItem>
                </SidebarMenu>
            </SidebarHeader>

            <SidebarContent>
                <SidebarGroup>
                    <SidebarGroupLabel>Analytics Views</SidebarGroupLabel>
                    <SidebarGroupContent>
                        <SidebarMenu>
                            {NAV_ITEMS.map((item) => (
                                <SidebarMenuItem key={item.id}>
                                    <SidebarMenuButton
                                        isActive={currentPage === item.id}
                                        onClick={() => onNavigate(item.id)}
                                        tooltip={item.label}
                                    >
                                        <item.icon className="size-4"/>
                                        <span>{item.label}</span>
                                        {item.badge && (
                                            <Badge
                                                variant="secondary"
                                                className="ml-auto h-5 rounded-sm px-1.5 text-xs"
                                            >
                                                {item.badge}
                                            </Badge>
                                        )}
                                    </SidebarMenuButton>
                                </SidebarMenuItem>
                            ))}
                        </SidebarMenu>
                    </SidebarGroupContent>
                </SidebarGroup>
            </SidebarContent>

            <SidebarFooter>
                <SidebarMenu>
                    <SidebarMenuItem>
                        <div className="flex items-center justify-between px-2 py-1">
                            <span className="text-xs text-muted-foreground">Theme</span>
                            <ModeToggle/>
                        </div>
                    </SidebarMenuItem>
                </SidebarMenu>
            </SidebarFooter>
        </Sidebar>
    )
}
