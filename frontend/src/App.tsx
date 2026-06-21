import { AppSidebar } from "@/components/layout/AppSidebar"
import { AgencyPage } from "@/components/dashboard/AgencyPage"
import { BacklogPage } from "@/components/dashboard/BacklogPage"
import { BoroughPage } from "@/components/dashboard/BoroughPage"
import { ComplaintsPage } from "@/components/dashboard/ComplaintsPage"
import { OverviewDashboard } from "@/components/dashboard/OverviewDashboard"
import type { NavPage } from "@/types"
import { useState } from "react"
import {
  SidebarInset,
  SidebarProvider,
  SidebarTrigger,
} from "@/components/ui/sidebar.tsx"
import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbList,
  BreadcrumbPage,
  BreadcrumbSeparator,
} from "@/components/ui/breadcrumb.tsx"
import { Separator } from "@/components/ui/separator.tsx"

const PAGE_LABELS: Record<NavPage, string> = {
  overview: "Executive Overview",
  agency: "Agency Performance",
  complaints: "Complaint Trends",
  geo: "Geographic View",
  backlog: "Backlog & Operations",
  sla: "SLA Performance",
  "borough-heatmap": "Borough Complaint Heatmap",
}

export function App() {
  const [currentPage, setCurrentPage] = useState<NavPage>("overview")

  return (
    <SidebarProvider>
      <AppSidebar currentPage={currentPage} onNavigate={setCurrentPage} />
      <SidebarInset>
        <header className="flex h-14 shrink-0 items-center gap-2 border-b px-4">
          <SidebarTrigger className="-ml-1" />
          <Separator orientation="vertical" className="mr-2 h-4" />
          <Breadcrumb>
            <BreadcrumbList>
              <BreadcrumbItem className="hidden md:block">
                <span className="text-sm text-muted-foreground">
                  NYC 311 Pipeline
                </span>
              </BreadcrumbItem>
              <BreadcrumbSeparator className="hidden md:block" />
              <BreadcrumbItem>
                <BreadcrumbPage>{PAGE_LABELS[currentPage]}</BreadcrumbPage>
              </BreadcrumbItem>
            </BreadcrumbList>
          </Breadcrumb>
        </header>

        <main className="flex-1 overflow-y-auto p-6">
          {currentPage === "overview" && <OverviewDashboard />}
          {currentPage === "agency" && <AgencyPage />}
          {currentPage === "complaints" && <ComplaintsPage />}
          {currentPage === "backlog" && <BacklogPage />}
          {currentPage === "borough-heatmap" && <BoroughPage />}
        </main>
      </SidebarInset>
    </SidebarProvider>
  )
}

export default App
