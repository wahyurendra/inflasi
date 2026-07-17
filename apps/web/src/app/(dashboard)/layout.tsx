import type { Metadata } from "next";
import { Sidebar } from "@/components/layout/sidebar";
import { Header } from "@/components/layout/header";
import { CopilotDashboard } from "@/components/ai/copilot-dashboard";
import { RouteGuard } from "@/components/layout/route-guard";
import { Providers } from "@/components/providers";
import { ApprovalPopup } from "@/components/gamification/approval-popup";

// Authenticated app surfaces — keep out of search indexes.
export const metadata: Metadata = {
  robots: { index: false, follow: false },
};

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <Providers>
      <RouteGuard>
        <div className="dashboard-theme flex h-screen bg-background text-foreground text-[13px]">
          <Sidebar />
          <div className="flex-1 flex flex-col overflow-hidden">
            <Header />
            <main className="flex-1 overflow-y-auto p-4 md:p-6">{children}</main>
          </div>
          <CopilotDashboard />
          <ApprovalPopup />
        </div>
      </RouteGuard>
    </Providers>
  );
}
