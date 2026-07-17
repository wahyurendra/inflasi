"use client";

import { useEffect, useRef, useState } from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import {
  useLatestApprovalNotification,
  useMarkAsRead,
} from "@/hooks/use-notifications";
import { Award, Flame, PartyPopper } from "lucide-react";

interface ApprovalData {
  reportId: string;
  pointsEarned: number;
  totalPoints: number;
  currentStreak: number;
  newBadges: { code: string; name: string; icon: string; description: string }[];
}

export function ApprovalPopup() {
  const { data: notification } = useLatestApprovalNotification();
  const markAsRead = useMarkAsRead();
  const [active, setActive] = useState<{ id: string; data: ApprovalData } | null>(null);
  const handledIds = useRef<Set<string>>(new Set());

  useEffect(() => {
    if (!notification || active || handledIds.current.has(notification.id)) return;
    handledIds.current.add(notification.id);
    setActive({ id: notification.id, data: notification.data });
    markAsRead.mutate([notification.id]);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [notification, active]);

  const close = () => setActive(null);

  return (
    <Dialog open={!!active} onOpenChange={(open) => !open && close()}>
      <DialogContent className="sm:max-w-md text-center">
        <DialogHeader className="items-center">
          <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-full bg-primary/10 text-primary mb-2">
            <PartyPopper className="h-7 w-7" />
          </div>
          <DialogTitle className="text-xl">Laporan Disetujui!</DialogTitle>
          <DialogDescription>
            Terima kasih atas kontribusi Anda memantau harga pangan.
          </DialogDescription>
        </DialogHeader>

        {active && (
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-3">
              <div className="rounded-xl border bg-card p-4">
                <Award className="h-5 w-5 mx-auto text-yellow-500 mb-1" />
                <p className="text-2xl font-bold">+{active.data.pointsEarned}</p>
                <p className="text-xs text-muted-foreground">
                  Poin (total {active.data.totalPoints})
                </p>
              </div>
              <div className="rounded-xl border bg-card p-4">
                <Flame className="h-5 w-5 mx-auto text-orange-500 mb-1" />
                <p className="text-2xl font-bold">{active.data.currentStreak}</p>
                <p className="text-xs text-muted-foreground">Hari beruntun</p>
              </div>
            </div>

            {active.data.newBadges.length > 0 && (
              <div className="space-y-2 text-left">
                <p className="text-sm font-medium text-center">Badge baru diperoleh</p>
                {active.data.newBadges.map((b) => (
                  <div
                    key={b.code}
                    className="flex items-center gap-3 rounded-lg border bg-muted/40 p-3"
                  >
                    <Award className="h-5 w-5 text-primary shrink-0" />
                    <div>
                      <p className="text-sm font-semibold">{b.name}</p>
                      <p className="text-xs text-muted-foreground">{b.description}</p>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        <DialogFooter>
          <Button className="w-full" onClick={close}>
            Lanjutkan Melapor
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
