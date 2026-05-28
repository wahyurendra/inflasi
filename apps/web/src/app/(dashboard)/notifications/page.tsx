"use client";

import { useNotifications, useMarkAsRead } from "@/hooks/use-notifications";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Bell,
  CheckCircle,
  FileText,
  Award,
  AlertTriangle,
  Check,
} from "lucide-react";

const typeIcons: Record<string, typeof Bell> = {
  report_received: FileText,
  report_approved: CheckCircle,
  report_rejected: AlertTriangle,
  price_alert: Bell,
  badge_earned: Award,
};

const typeLabels: Record<string, string> = {
  report_received: "Laporan",
  report_approved: "Disetujui",
  report_rejected: "Ditolak",
  price_alert: "Alert",
  badge_earned: "Badge",
};

interface Notification {
  id: string;
  type: string;
  title: string;
  message: string;
  isRead: boolean;
  createdAt: string;
}

export default function NotificationsPage() {
  const { data } = useNotifications();
  const markAsRead = useMarkAsRead();

  const notifications: Notification[] = data?.data || [];

  const handleMarkAllRead = () => {
    const unreadIds = notifications.filter((n) => !n.isRead).map((n) => n.id);
    if (unreadIds.length > 0) {
      markAsRead.mutate(unreadIds);
    }
  };

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-lg font-bold text-foreground flex items-center gap-2">
          <Bell className="h-5 w-5 text-primary" />
          Notifikasi
        </h1>
        <Button
          variant="outline"
          size="sm"
          onClick={handleMarkAllRead}
          disabled={markAsRead.isPending}
        >
          <Check className="h-4 w-4 mr-1" />
          Tandai Semua Dibaca
        </Button>
      </div>

      <div className="space-y-2">
        {notifications.length === 0 && (
          <div className="bg-card rounded-xl border p-8 text-center text-muted-foreground">
            <Bell className="h-8 w-8 mx-auto mb-2 opacity-50" />
            <p>Belum ada notifikasi</p>
          </div>
        )}

        {notifications.map((notif) => {
          const Icon = typeIcons[notif.type] || Bell;
          return (
            <div
              key={notif.id}
              className={`bg-card rounded-xl border p-4 flex items-start gap-3 ${
                !notif.isRead ? "border-primary/30 bg-primary/5" : ""
              }`}
            >
              <Icon className={`h-5 w-5 mt-0.5 ${!notif.isRead ? "text-primary" : "text-muted-foreground"}`} />
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1">
                  <p className="text-sm font-medium">{notif.title}</p>
                  <Badge variant="outline" className="text-xs">
                    {typeLabels[notif.type] || notif.type}
                  </Badge>
                  {!notif.isRead && (
                    <span className="h-2 w-2 rounded-full bg-primary" />
                  )}
                </div>
                <p className="text-sm text-muted-foreground">{notif.message}</p>
                <p className="text-xs text-muted-foreground mt-1">
                  {new Date(notif.createdAt).toLocaleDateString("id-ID", {
                    day: "numeric",
                    month: "short",
                    year: "numeric",
                    hour: "2-digit",
                    minute: "2-digit",
                  })}
                </p>
              </div>
              {!notif.isRead && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => markAsRead.mutate([notif.id])}
                >
                  <Check className="h-3 w-3" />
                </Button>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
