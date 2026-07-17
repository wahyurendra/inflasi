"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";

export function useNotifications(page = 1) {
  return useQuery({
    queryKey: ["notifications", page],
    queryFn: async () => {
      const res = await fetch(`/api/notifications?page=${page}`);
      if (!res.ok) throw new Error("Failed to fetch notifications");
      return res.json();
    },
  });
}

export function useUnreadCount() {
  return useQuery({
    queryKey: ["notification-count"],
    queryFn: async () => {
      const res = await fetch("/api/notifications/count");
      if (!res.ok) return { count: 0 };
      return res.json();
    },
    refetchInterval: 30000,
  });
}

interface ApprovalNotification {
  id: string;
  type: string;
  isRead: boolean;
  data: {
    reportId: string;
    pointsEarned: number;
    totalPoints: number;
    currentStreak: number;
    newBadges: { code: string; name: string; icon: string; description: string }[];
  };
}

/** Polls for the newest unread "report_approved" notification, for the
 * approval popup. Reuses the same 30s cadence as `useUnreadCount`. */
export function useLatestApprovalNotification() {
  return useQuery({
    queryKey: ["notifications", "approval-poll"],
    queryFn: async () => {
      const res = await fetch("/api/notifications?page=1&limit=5");
      if (!res.ok) return { data: [] };
      return res.json();
    },
    refetchInterval: 30000,
    select: (json: { data?: ApprovalNotification[] }) =>
      json.data?.find((n) => n.type === "report_approved" && !n.isRead) ?? null,
  });
}

export function useMarkAsRead() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (ids?: string[]) => {
      const res = await fetch("/api/notifications", {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ids }),
      });
      if (!res.ok) throw new Error("Failed to mark as read");
      return res.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["notifications"] });
      queryClient.invalidateQueries({ queryKey: ["notification-count"] });
    },
  });
}
