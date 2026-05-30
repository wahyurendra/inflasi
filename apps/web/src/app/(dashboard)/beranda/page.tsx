"use client";

import { useAuth } from "@/hooks/use-auth";
import { ReporterHome } from "./views/reporter-home";
import { OfficerHome } from "./views/officer-home";
import { AnalystHome } from "./views/analyst-home";
import { AdminHome } from "./views/admin-home";

export default function BerandaPage() {
  const { role, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div className="space-y-3">
        <div className="h-6 w-48 bg-muted rounded animate-pulse" />
        <div className="h-32 bg-muted rounded animate-pulse" />
      </div>
    );
  }

  switch (role) {
    case "ADMIN":
      return <AdminHome />;
    case "GOVERNMENT_ANALYST":
      return <AnalystHome />;
    case "REGIONAL_OFFICER":
      return <OfficerHome />;
    case "REPORTER":
      return <ReporterHome />;
    default:
      return <AnalystHome />;
  }
}
