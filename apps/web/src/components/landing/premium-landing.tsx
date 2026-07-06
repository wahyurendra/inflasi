"use client";

import { ReactNode, useEffect, useState } from "react";
import Image from "next/image";
import Link from "next/link";
import { motion, useReducedMotion } from "framer-motion";
import {
  Area,
  AreaChart,
  CartesianGrid,
  Line,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import {
  ArrowRight,
  ArrowUpRight,
  BadgeCheck,
  Bell,
  Building2,
  Camera,
  ChevronDown,
  Landmark,
  LineChart as LineChartIcon,
  MapPin,
  Menu,
  ScanSearch,
  ShieldCheck,
  Sprout,
  Trophy,
  Users,
  Wheat,
  X,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

type Status = "stable" | "watch" | "spike";

const navLinks = [
  { label: "Dashboard", href: "/welcome#dashboard" },
  { label: "Peta Harga", href: "/welcome#heatmap" },
  { label: "Prediksi AI", href: "/welcome#forecasting" },
  { label: "Ekosistem", href: "/welcome#ecosystem" },
  { label: "Blog", href: "/blog" },
];

/* Kartu standar landing: solid + hairline, tanpa backdrop-filter supaya ringan
   saat dipakai puluhan kali dalam satu halaman. liquid-glass hanya untuk
   elemen hero yang benar-benar butuh efek kaca. */
const CARD = "rounded-2xl border border-white/10 bg-white/[0.035]";

/* Warna seri chart — tervalidasi (lightness band, chroma, CVD, kontras) di atas
   permukaan gelap landing. Jangan ganti dengan token tema tanpa validasi ulang. */
const CHART_HISTORY = "#4a9d6e";
const CHART_FORECAST = "#b8891e";

type ForecastPoint = { month: string; history: number | null; forecast: number | null };

interface CommodityForecast {
  name: string;
  series: ForecastPoint[];
  oneMonth: { value: string; badge: string; status: Status };
  threeMonth: { value: string; badge: string; status: Status };
  confidence: { value: string; badge: string; status: Status };
  anomaly: { value: string; badge: string; status: Status };
}

const FORECASTS: Record<string, CommodityForecast> = {
  "Cabai Merah": {
    name: "Cabai Merah",
    series: [
      { month: "Jan", history: 100, forecast: null },
      { month: "Feb", history: 104, forecast: null },
      { month: "Mar", history: 109, forecast: null },
      { month: "Apr", history: 116, forecast: null },
      { month: "Mei", history: 124, forecast: 124 },
      { month: "Jun", history: null, forecast: 133 },
      { month: "Jul", history: null, forecast: 141 },
      { month: "Agu", history: null, forecast: 148 },
    ],
    oneMonth: { value: "+7,3%", badge: "Waspada", status: "watch" },
    threeMonth: { value: "+19,4%", badge: "Risiko Tinggi", status: "spike" },
    confidence: { value: "91%", badge: "Tervalidasi", status: "stable" },
    anomaly: { value: "Papua — lonjakan", badge: "Lonjakan", status: "spike" },
  },
  Beras: {
    name: "Beras",
    series: [
      { month: "Jan", history: 100, forecast: null },
      { month: "Feb", history: 100, forecast: null },
      { month: "Mar", history: 101, forecast: null },
      { month: "Apr", history: 101, forecast: null },
      { month: "Mei", history: 102, forecast: 102 },
      { month: "Jun", history: null, forecast: 102 },
      { month: "Jul", history: null, forecast: 103 },
      { month: "Agu", history: null, forecast: 103 },
    ],
    oneMonth: { value: "+0,4%", badge: "Stabil", status: "stable" },
    threeMonth: { value: "+1,1%", badge: "Stabil", status: "stable" },
    confidence: { value: "94%", badge: "Tervalidasi", status: "stable" },
    anomaly: { value: "Tidak terdeteksi", badge: "Aman", status: "stable" },
  },
  Telur: {
    name: "Telur Ayam",
    series: [
      { month: "Jan", history: 100, forecast: null },
      { month: "Feb", history: 102, forecast: null },
      { month: "Mar", history: 105, forecast: null },
      { month: "Apr", history: 107, forecast: null },
      { month: "Mei", history: 110, forecast: 110 },
      { month: "Jun", history: null, forecast: 114 },
      { month: "Jul", history: null, forecast: 117 },
      { month: "Agu", history: null, forecast: 120 },
    ],
    oneMonth: { value: "+3,4%", badge: "Waspada", status: "watch" },
    threeMonth: { value: "+9,1%", badge: "Waspada", status: "watch" },
    confidence: { value: "88%", badge: "Tervalidasi", status: "stable" },
    anomaly: { value: "Sulsel — naik", badge: "Waspada", status: "watch" },
  },
  "Minyak Goreng": {
    name: "Minyak Goreng",
    series: [
      { month: "Jan", history: 100, forecast: null },
      { month: "Feb", history: 101, forecast: null },
      { month: "Mar", history: 103, forecast: null },
      { month: "Apr", history: 106, forecast: null },
      { month: "Mei", history: 109, forecast: 109 },
      { month: "Jun", history: null, forecast: 113 },
      { month: "Jul", history: null, forecast: 116 },
      { month: "Agu", history: null, forecast: 118 },
    ],
    oneMonth: { value: "+2,8%", badge: "Waspada", status: "watch" },
    threeMonth: { value: "+8,3%", badge: "Waspada", status: "watch" },
    confidence: { value: "86%", badge: "Tervalidasi", status: "stable" },
    anomaly: { value: "Sumut — pantau", badge: "Waspada", status: "watch" },
  },
};

function statusClass(status: Status) {
  if (status === "spike") return "bg-danger text-white border-danger/40";
  if (status === "watch") return "bg-warning text-secondary-foreground border-warning/40";
  return "bg-success text-white border-success/40";
}

function FadeIn({
  children,
  className,
  delay = 0,
}: {
  children: ReactNode;
  className?: string;
  delay?: number;
}) {
  const reduceMotion = useReducedMotion();

  return (
    <motion.div
      initial={reduceMotion ? false : { opacity: 0, y: 26 }}
      whileInView={reduceMotion ? undefined : { opacity: 1, y: 0 }}
      viewport={{ once: true, margin: "-80px" }}
      transition={{ duration: 0.65, delay, ease: [0.22, 1, 0.36, 1] }}
      className={className}
    >
      {children}
    </motion.div>
  );
}

function SectionHeading({
  eyebrow,
  title,
  subtitle,
  align = "center",
  className,
}: {
  eyebrow?: string;
  title: ReactNode;
  subtitle: string;
  align?: "center" | "left";
  className?: string;
}) {
  return (
    <FadeIn
      className={cn(
        "max-w-4xl",
        align === "center" ? "mx-auto text-center" : "text-left",
        className,
      )}
    >
      {eyebrow && (
        <p className="mb-4 text-xs font-semibold uppercase tracking-[0.28em] text-secondary/90">
          {eyebrow}
        </p>
      )}
      <h2 className="text-balance text-3xl font-medium leading-tight tracking-[-1.2px] text-foreground md:text-5xl">
        {title}
      </h2>
      <p
        className={cn(
          "mt-5 max-w-3xl text-base leading-7 text-muted-foreground md:text-lg",
          align === "center" && "mx-auto",
        )}
      >
        {subtitle}
      </p>
    </FadeIn>
  );
}

export function Navbar() {
  const [open, setOpen] = useState(false);

  useEffect(() => {
    if (!open) return;
    const onKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") setOpen(false);
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [open]);

  return (
    <nav className="fixed inset-x-0 top-0 z-50 border-b border-white/5 bg-background/80 backdrop-blur-xl">
      <div className="mx-auto flex max-w-7xl items-center justify-between gap-4 px-5 py-3.5 md:px-8">
        <Link href="/welcome" className="flex items-center gap-3" onClick={() => setOpen(false)}>
          <Image src="/logo.svg" alt="INFLASI ID" width={40} height={40} priority className="h-9 w-9 rounded-full" />
          <span className="text-lg font-bold tracking-tight text-foreground">inflasi.id</span>
          <span className="hidden rounded-full border border-white/10 px-2 py-1 text-[11px] text-muted-foreground lg:inline">
            Intelijen Pangan
          </span>
        </Link>

        <div className="hidden items-center gap-1 md:flex">
          {navLinks.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              className="rounded-full px-3.5 py-2 text-sm text-muted-foreground transition hover:bg-white/5 hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
            >
              {link.label}
            </Link>
          ))}
        </div>

        <div className="flex items-center gap-2">
          <Link href="/partner" className="hidden text-sm text-muted-foreground transition hover:text-foreground lg:inline">
            Jadi Mitra
          </Link>
          <Button asChild className="hidden rounded-full bg-secondary px-5 text-sm font-semibold text-secondary-foreground hover:bg-secondary/90 sm:inline-flex">
            <Link href="/login">Buka Dashboard</Link>
          </Button>
          <button
            type="button"
            onClick={() => setOpen((v) => !v)}
            aria-expanded={open}
            aria-label={open ? "Tutup menu" : "Buka menu"}
            className="inline-flex h-10 w-10 items-center justify-center rounded-full border border-white/10 text-foreground transition hover:bg-white/5 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring md:hidden"
          >
            {open ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
          </button>
        </div>
      </div>

      {/* Menu mobile */}
      {open && (
        <div className="border-t border-white/5 bg-background/95 px-5 pb-5 pt-2 backdrop-blur-xl md:hidden">
          <div className="flex flex-col gap-1">
            {navLinks.map((link) => (
              <Link
                key={link.href}
                href={link.href}
                onClick={() => setOpen(false)}
                className="rounded-xl px-4 py-3 text-sm font-medium text-muted-foreground transition hover:bg-white/5 hover:text-foreground"
              >
                {link.label}
              </Link>
            ))}
            <Link
              href="/partner"
              onClick={() => setOpen(false)}
              className="rounded-xl px-4 py-3 text-sm font-medium text-muted-foreground transition hover:bg-white/5 hover:text-foreground"
            >
              Jadi Mitra
            </Link>
          </div>
          <Button asChild className="mt-3 w-full rounded-full bg-secondary text-sm font-semibold text-secondary-foreground hover:bg-secondary/90">
            <Link href="/login" onClick={() => setOpen(false)}>Buka Dashboard</Link>
          </Button>
        </div>
      )}
    </nav>
  );
}

export function MetricCard({
  value,
  label,
  highlighted,
}: {
  value: string;
  label: string;
  highlighted?: boolean;
}) {
  return (
    <div className={cn(CARD, "px-5 py-4 text-left", highlighted && "gold-glow border-secondary/25")}>
      <p className="text-2xl font-bold text-foreground">{value}</p>
      <p className="mt-1 text-sm text-muted-foreground">{label}</p>
    </div>
  );
}

function ChartTooltip({ active, payload, label }: { active?: boolean; payload?: any[]; label?: string }) {
  if (!active || !payload?.length) return null;

  return (
    <div className="rounded-xl border border-white/10 bg-background/95 px-3 py-2 text-xs shadow-2xl">
      <p className="mb-1 font-semibold text-foreground">{label}</p>
      {payload.map((item) => (
        <p key={item.dataKey} className="text-muted-foreground">
          <span style={{ color: item.color }}>●</span> {item.name || item.dataKey}: {item.value}
        </p>
      ))}
    </div>
  );
}

/* Frame browser bernuansa terang — screenshot produk memakai tema terang,
   jadi chrome-nya ikut terang agar menyatu seperti jendela aplikasi asli. */
function BrowserFrame({
  children,
  url = "app.inflasi.id/wilayah",
  className,
}: {
  children: ReactNode;
  url?: string;
  className?: string;
}) {
  return (
    <div
      className={cn(
        "overflow-hidden rounded-2xl border border-white/15 bg-white shadow-[0_40px_120px_-24px_rgba(0,0,0,0.65)]",
        className,
      )}
    >
      {/* Chrome browser */}
      <div className="flex items-center gap-3 border-b border-black/10 bg-[#f2f5f3] px-4 py-3">
        <div className="flex items-center gap-1.5">
          <span className="h-3 w-3 rounded-full bg-[#ff5f57]" />
          <span className="h-3 w-3 rounded-full bg-[#febc2e]" />
          <span className="h-3 w-3 rounded-full bg-[#28c840]" />
        </div>
        <div className="mx-auto flex max-w-sm flex-1 items-center justify-center gap-2 rounded-md border border-black/10 bg-white px-3 py-1.5">
          <ShieldCheck className="h-3 w-3 text-[#2f7d4f]" />
          <span className="truncate text-[11px] text-slate-500">{url}</span>
        </div>
        <span className="hidden items-center gap-1.5 rounded-full border border-[#2f7d4f]/25 bg-[#2f7d4f]/10 px-2.5 py-1 text-[10px] font-semibold text-[#2f7d4f] sm:inline-flex">
          <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-[#2f7d4f]" />
          Live
        </span>
      </div>
      {children}
    </div>
  );
}

export function DashboardPreview() {
  return (
    <div id="dashboard" className="relative">
      {/* Cahaya ambient di belakang product shot — gradien radial sudah lembut,
          tidak perlu filter blur tambahan */}
      <div
        aria-hidden
        className="pointer-events-none absolute -inset-x-12 -inset-y-8 bg-[radial-gradient(ellipse_at_center,hsl(var(--primary)/0.24),transparent_62%)]"
      />

      {/* Sedikit perspektif statis supaya terasa seperti jendela produk sungguhan */}
      <div className="relative lg:[transform:perspective(1400px)_rotateY(-5deg)_rotateX(1.5deg)]">
        <BrowserFrame className="green-glow">
          <Image
            src="/dashboard-heatmap.png"
            alt="Dashboard Peta Tekanan Harga inflasi.id — heatmap nasional, ranking provinsi, dan deteksi tekanan harga pangan secara real-time"
            width={1806}
            height={1012}
            priority
            className="w-full"
          />
        </BrowserFrame>
      </div>

      {/* Chip statistik mengambang */}
      <div className="pointer-events-none absolute -left-5 top-10 hidden rounded-2xl border border-white/10 bg-background/95 px-4 py-3 shadow-2xl md:block">
        <p className="text-[10px] uppercase tracking-[0.18em] text-secondary">Cakupan</p>
        <p className="mt-1 text-lg font-bold text-foreground">38 Provinsi</p>
        <p className="text-[11px] text-muted-foreground">Heatmap live</p>
      </div>
      <div className="pointer-events-none absolute -bottom-5 -right-3 hidden rounded-2xl border border-white/10 bg-background/95 px-4 py-3 shadow-2xl md:block">
        <div className="flex items-center gap-2">
          <Bell className="h-4 w-4 text-warning" />
          <p className="text-[10px] uppercase tracking-[0.18em] text-warning">Alert Aktif</p>
        </div>
        <p className="mt-1 text-lg font-bold text-foreground">20 Sinyal</p>
        <p className="text-[11px] text-muted-foreground">Pemantauan real-time</p>
      </div>
    </div>
  );
}

/* Ticker harga komoditas — data ilustratif, dirender dua kali untuk loop
   mulus. Saat reduced-motion, jatuh ke baris statis yang bisa digulir. */
function HeroTicker() {
  const reduceMotion = useReducedMotion();
  const items: { name: string; change: string; status: Status }[] = [
    { name: "Beras", change: "+0,4%", status: "stable" },
    { name: "Cabai Merah", change: "+7,3%", status: "spike" },
    { name: "Telur Ayam", change: "+3,4%", status: "watch" },
    { name: "Minyak Goreng", change: "+2,8%", status: "watch" },
    { name: "Bawang Merah", change: "+1,9%", status: "watch" },
    { name: "Gula Pasir", change: "+0,8%", status: "stable" },
    { name: "Daging Ayam", change: "-0,6%", status: "stable" },
    { name: "Tomat", change: "+4,1%", status: "watch" },
  ];

  const dotClass = (status: Status) =>
    status === "spike" ? "bg-danger" : status === "watch" ? "bg-warning" : "bg-success";

  const row = (ariaHidden: boolean) => (
    <div aria-hidden={ariaHidden || undefined} className="flex shrink-0 items-center">
      {items.map((item) => (
        <span key={item.name} className="flex items-center gap-2 whitespace-nowrap px-5 text-sm text-muted-foreground">
          <span className={cn("h-1.5 w-1.5 rounded-full", dotClass(item.status))} />
          {item.name}
          <span className={cn("font-semibold", item.status === "spike" ? "text-danger" : item.status === "watch" ? "text-warning" : "text-success")}>
            {item.change}
          </span>
        </span>
      ))}
    </div>
  );

  return (
    <div className="relative overflow-hidden border-y border-white/8 py-3.5 [mask-image:linear-gradient(90deg,transparent,#000_8%,#000_92%,transparent)]">
      {reduceMotion ? (
        <div className="no-scrollbar overflow-x-auto">{row(false)}</div>
      ) : (
        <div className="flex w-max [animation:ticker-scroll_36s_linear_infinite]">
          {row(false)}
          {row(true)}
        </div>
      )}
    </div>
  );
}

/* Latar hero statis: seluruh nuansa aurora digambar sebagai gradien radial
   biasa — tanpa filter blur, tanpa animasi berjalan, tanpa parallax — supaya
   hero tidak membebani main thread saat scroll. Spot disusun asimetris
   mengikuti layout split: hijau di sisi copy, emas di sisi produk. */
function HeroBackground() {
  return (
    <div aria-hidden className="pointer-events-none absolute inset-0 overflow-hidden">
      <div
        className="absolute inset-0"
        style={{
          background: [
            "radial-gradient(circle at 28% 0%, hsl(var(--primary) / 0.26), transparent 58%)",
            "radial-gradient(ellipse 40% 36% at 12% 40%, hsl(var(--primary) / 0.14), transparent 70%)",
            "radial-gradient(ellipse 38% 32% at 88% 28%, hsl(var(--secondary) / 0.09), transparent 70%)",
          ].join(", "),
        }}
      />

      {/* Grid teknikal statis */}
      <div className="absolute inset-0 landing-grid opacity-60 [animation:none]" />

      {/* Vignette tepi + fade bawah ke halaman */}
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,transparent_55%,hsl(var(--background)/0.85)_100%)]" />
      <div className="absolute inset-x-0 bottom-0 h-40 bg-gradient-to-b from-transparent to-background" />
    </div>
  );
}

export function Hero() {
  const reduceMotion = useReducedMotion();

  const stats = [
    ["38", "Provinsi"],
    ["10+", "Komoditas"],
    ["24/7", "Real-time"],
    ["1–3 bln", "Prediksi AI"],
  ] as const;

  return (
    <section className="relative overflow-hidden pt-28 md:pt-32">
      <HeroBackground />

      <div className="relative z-10 mx-auto max-w-7xl px-5 pb-14 md:px-8">
        <div className="grid items-center gap-12 lg:grid-cols-[1.02fr_0.98fr] lg:gap-10">
          {/* Kolom copy */}
          <div className="text-center lg:text-left">
            <motion.div
              initial={reduceMotion ? false : { opacity: 0, y: 10 }}
              animate={reduceMotion ? undefined : { opacity: 1, y: 0 }}
              transition={{ duration: 0.5 }}
              className="mb-6 inline-flex items-center gap-3 rounded-full border border-white/10 bg-white/[0.04] px-4 py-2 text-sm text-muted-foreground"
            >
              <span className="relative flex h-2 w-2">
                <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-success opacity-60" />
                <span className="relative inline-flex h-2 w-2 rounded-full bg-success" />
              </span>
              Live · 38 provinsi terpantau
            </motion.div>

            <motion.h1
              initial={reduceMotion ? false : { opacity: 0, y: 20 }}
              animate={reduceMotion ? undefined : { opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.08 }}
              className="text-balance text-4xl font-medium leading-[1.06] tracking-[-1.8px] text-foreground sm:text-5xl md:text-6xl xl:text-7xl xl:tracking-[-2.5px]"
            >
              Baca pergerakan harga pangan, <span className="font-serif-accent text-secondary">sebelum jadi krisis.</span>
            </motion.h1>

            <motion.p
              initial={reduceMotion ? false : { opacity: 0, y: 20 }}
              animate={reduceMotion ? undefined : { opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.16 }}
              className="mx-auto mt-6 max-w-xl text-base leading-7 text-hero-subtitle opacity-90 md:text-lg lg:mx-0"
            >
              Intelijen inflasi pangan Indonesia: harga real-time, deteksi anomali,
              dan prediksi 1–3 bulan — ditenagai laporan warga tervalidasi dan AI.
            </motion.p>

            <motion.div
              initial={reduceMotion ? false : { opacity: 0, y: 20 }}
              animate={reduceMotion ? undefined : { opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.24 }}
              className="mt-8 flex flex-col items-center gap-3 sm:flex-row sm:justify-center lg:justify-start"
            >
              <Button asChild className="h-12 rounded-full bg-secondary px-8 text-base font-semibold text-secondary-foreground transition-transform hover:scale-[1.02] hover:bg-secondary/90 active:scale-[0.98]">
                <Link href="/login">Jelajahi Dashboard <ArrowRight className="ml-2 h-4 w-4" /></Link>
              </Button>
              <Button asChild variant="outline" className="h-12 rounded-full border-white/15 bg-white/5 px-8 text-base font-medium text-foreground hover:bg-white/10 hover:text-foreground">
                <Link href="#heatmap">Lihat Peta Nasional</Link>
              </Button>
            </motion.div>

            {/* Baris statistik kompak menggantikan grid kartu */}
            <motion.dl
              initial={reduceMotion ? false : { opacity: 0, y: 24 }}
              animate={reduceMotion ? undefined : { opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.32 }}
              className="mx-auto mt-10 grid max-w-xs grid-cols-2 gap-x-6 gap-y-5 sm:mx-0 sm:flex sm:max-w-none sm:items-center sm:justify-center sm:gap-8 lg:justify-start"
            >
              {stats.map(([value, label], i) => (
                <div key={label} className={cn("text-center lg:text-left", i > 0 && "sm:border-l sm:border-white/10 sm:pl-8")}>
                  <dt className="sr-only">{label}</dt>
                  <dd className="whitespace-nowrap text-xl font-bold text-foreground sm:text-2xl">{value}</dd>
                  <dd className="mt-0.5 whitespace-nowrap text-xs text-muted-foreground sm:text-sm">{label}</dd>
                </div>
              ))}
            </motion.dl>
          </div>

          {/* Kolom produk */}
          <motion.div
            initial={reduceMotion ? false : { opacity: 0, y: 32 }}
            animate={reduceMotion ? undefined : { opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.3 }}
          >
            <DashboardPreview />
          </motion.div>
        </div>
      </div>

      {/* Ticker harga komoditas */}
      <motion.div
        initial={reduceMotion ? false : { opacity: 0 }}
        animate={reduceMotion ? undefined : { opacity: 1 }}
        transition={{ duration: 0.8, delay: 0.5 }}
        className="relative z-10"
      >
        <HeroTicker />
      </motion.div>
    </section>
  );
}

export function ProblemSection() {
  return (
    <section id="problem" className="px-5 py-20 md:px-8 md:py-28">
      <div className="mx-auto max-w-7xl">
        <SectionHeading
          align="left"
          eyebrow="Masalah"
          title={
            <>
              Indonesia masih punya <span className="font-serif-accent text-secondary">titik buta</span> harga pangan.
            </>
          }
          subtitle="Harga pangan bisa bergerak lebih cepat daripada siklus pelaporan resmi. inflasi.id menutup celah visibilitas itu dengan data komunitas, validasi berlapis, dan prediksi AI."
        />

        <div className="mt-12 grid gap-4 md:grid-cols-3">
          {[
            ["84%", "Wilayah belum memiliki data harga harian"],
            ["432", "Kabupaten/kota di luar jangkauan pemantauan harian"],
            ["0", "Data akhir pekan & hari libur dari sistem tradisional"],
          ].map(([value, label], index) => (
            <FadeIn key={value} delay={index * 0.08} className={cn(CARD, "rounded-3xl p-7")}>
              <p className="text-5xl font-bold text-foreground">{value}</p>
              <p className="mt-4 text-sm leading-6 text-muted-foreground">{label}</p>
            </FadeIn>
          ))}
        </div>

        <FadeIn className="liquid-glass gold-glow mt-10 rounded-3xl p-6 md:p-8">
          <div className="mb-8 flex flex-col justify-between gap-4 md:flex-row md:items-end">
            <div>
              <h3 className="text-2xl font-semibold text-foreground">Komoditas sama. Realitas berbeda.</h3>
              <p className="mt-2 max-w-2xl text-sm leading-6 text-muted-foreground">
                Visibilitas real-time menyingkap jurang harga antarwilayah sebelum menjadi titik buta kebijakan.
              </p>
            </div>
            <span className="rounded-full border border-secondary/25 bg-secondary/10 px-4 py-2 text-sm font-semibold text-secondary">Cabai Merah</span>
          </div>
          <div className="grid gap-6 md:grid-cols-[1fr_1.2fr_1fr] md:items-center">
            <ComparisonCard region="Papua" price="Rp200.000/kg" status="Lonjakan Ekstrem" tone="spike" />
            <div className="relative h-20">
              <div className="absolute left-4 right-4 top-1/2 h-1 -translate-y-1/2 rounded-full bg-gradient-to-r from-success via-warning to-danger" />
              <span className="absolute left-3 top-1/2 h-5 w-5 -translate-y-1/2 rounded-full border-4 border-background bg-success" />
              <span className="absolute right-3 top-1/2 h-5 w-5 -translate-y-1/2 rounded-full border-4 border-background bg-danger" />
              <p className="absolute inset-x-0 bottom-0 text-center text-xs text-muted-foreground">Selisih regional Rp185 ribu/kg</p>
            </div>
            <ComparisonCard region="Brebes" price="Rp15.000/kg" status="Pasokan Stabil" tone="stable" />
          </div>
        </FadeIn>
      </div>
    </section>
  );
}

function ComparisonCard({ region, price, status, tone }: { region: string; price: string; status: string; tone: Status }) {
  return (
    <div className={cn(CARD, "p-5")}>
      <p className="text-sm text-muted-foreground">{region}</p>
      <p className="mt-2 text-lg font-semibold text-foreground">Cabai Merah</p>
      <p className="mt-4 text-3xl font-bold text-foreground">{price}</p>
      <span className={cn("mt-4 inline-flex rounded-full border px-3 py-1 text-xs font-semibold", statusClass(tone))}>{status}</span>
    </div>
  );
}

export function HowItWorks() {
  const steps = [
    [Camera, "Warga melapor harga", "Foto struk, harga komoditas, dan lokasi pasar dalam hitungan detik."],
    [MapPin, "Validasi GPS & AI", "Geofencing, peer review, dan deteksi anomali menyaring data tidak wajar."],
    [ShieldCheck, "Agregasi data", "Data publik, crowdsource, dan referensi resmi dinormalisasi per wilayah."],
    [LineChartIcon, "Prediksi inflasi", "Model AI membaca tren, risiko lonjakan, dan proyeksi 1–3 bulan."],
    [Bell, "Dashboard & peringatan", "Pemerintah, masyarakat, dan institusi mendapat peringatan dini real-time."],
  ] as const;

  return (
    <section className="px-5 py-20 md:px-8 md:py-28">
      <div className="mx-auto max-w-7xl">
        <SectionHeading
          eyebrow="Cara Kerja"
          title="Dari laporan pasar menjadi intelijen nasional."
          subtitle="Setiap laporan warga menjadi bagian dari sinyal harga pangan yang tervalidasi."
        />
        <div className="relative mt-14">
          {/* Garis alur penghubung antar-langkah (desktop) */}
          <div aria-hidden className="absolute left-0 right-0 top-10 hidden h-px bg-gradient-to-r from-transparent via-secondary/30 to-transparent lg:block" />
          <div className="grid gap-4 lg:grid-cols-5">
            {steps.map(([Icon, title, description], index) => (
              <FadeIn key={title} delay={index * 0.06} className={cn(CARD, "relative p-6 transition hover:border-secondary/30")}>
                <div className="mb-6 flex items-center justify-between">
                  <span className="flex h-11 w-11 items-center justify-center rounded-xl bg-secondary/12 text-secondary">
                    <Icon className="h-5 w-5" />
                  </span>
                  <span className="text-sm font-semibold text-secondary">0{index + 1}</span>
                </div>
                <h3 className="text-lg font-semibold text-foreground">{title}</h3>
                <p className="mt-3 text-sm leading-6 text-muted-foreground">{description}</p>
              </FadeIn>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}

export function ForecastingSection() {
  const [commodity, setCommodity] = useState<keyof typeof FORECASTS>("Cabai Merah");
  const active = FORECASTS[commodity];

  const metrics: { label: string; value: string; badge: string; status: Status }[] = [
    { label: "Prediksi 1 Bulan", value: active.oneMonth.value, badge: active.oneMonth.badge, status: active.oneMonth.status },
    { label: "Prediksi 3 Bulan", value: active.threeMonth.value, badge: active.threeMonth.badge, status: active.threeMonth.status },
    { label: "Keyakinan Model", value: active.confidence.value, badge: active.confidence.badge, status: active.confidence.status },
    { label: "Anomali Terdeteksi", value: active.anomaly.value, badge: active.anomaly.badge, status: active.anomaly.status },
  ];

  return (
    <section id="forecasting" className="relative px-5 py-20 md:px-8 md:py-28">
      <div aria-hidden className="pointer-events-none absolute inset-x-0 top-20 h-80 bg-[radial-gradient(circle,hsl(var(--secondary)/0.10),transparent_62%)]" />
      <div className="relative mx-auto max-w-7xl">
        <SectionHeading
          eyebrow="Prediksi AI"
          title={
            <>
              Kenali tekanan inflasi <span className="font-serif-accent text-secondary">sebelum</span> menjadi krisis.
            </>
          }
          subtitle="inflasi.id memadukan riwayat harga, sinyal regional, laporan crowdsourced, dan deteksi anomali untuk mengidentifikasi tekanan inflasi lebih awal."
        />
        <div className="mt-14 grid items-stretch gap-5 lg:grid-cols-[1.45fr_0.85fr]">
          <FadeIn className={cn(CARD, "flex flex-col rounded-3xl p-5 md:p-7")}>
            <div className="mb-5 flex flex-wrap items-center justify-between gap-3">
              <div>
                <p className="text-lg font-semibold text-foreground">Model Prediksi</p>
                <p className="text-sm text-muted-foreground">Indeks harga {active.name} (Jan = 100) · garis solid historis, putus-putus proyeksi</p>
              </div>
              <div className="flex flex-wrap gap-2">
                {(Object.keys(FORECASTS) as (keyof typeof FORECASTS)[]).map((item) => (
                  <button
                    key={item}
                    onClick={() => setCommodity(item)}
                    aria-pressed={commodity === item}
                    className={cn(
                      "rounded-full border px-3 py-1.5 text-xs font-semibold transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
                      commodity === item ? "border-secondary/40 bg-secondary text-secondary-foreground" : "border-white/10 bg-white/5 text-muted-foreground hover:text-foreground"
                    )}
                  >
                    {item}
                  </button>
                ))}
              </div>
            </div>
            <ResponsiveContainer width="100%" height={330}>
              <AreaChart data={active.series} margin={{ top: 12, right: 18, left: -14, bottom: 0 }}>
                <defs>
                  <linearGradient id="forecastFill" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor={CHART_FORECAST} stopOpacity={0.24} />
                    <stop offset="100%" stopColor={CHART_FORECAST} stopOpacity={0.02} />
                  </linearGradient>
                </defs>
                <CartesianGrid stroke="hsl(var(--foreground) / 0.06)" vertical={false} />
                <XAxis dataKey="month" tick={{ fill: "hsl(var(--muted-foreground))", fontSize: 12 }} tickLine={false} axisLine={false} />
                <YAxis domain={["dataMin - 4", "dataMax + 6"]} tick={{ fill: "hsl(var(--muted-foreground))", fontSize: 12 }} tickLine={false} axisLine={false} />
                <Tooltip content={<ChartTooltip />} />
                <Area type="monotone" dataKey="forecast" name="Proyeksi" stroke={CHART_FORECAST} strokeDasharray="7 5" fill="url(#forecastFill)" strokeWidth={2} connectNulls />
                <Line type="monotone" dataKey="history" name="Historis" stroke={CHART_HISTORY} strokeWidth={2} dot={false} />
              </AreaChart>
            </ResponsiveContainer>
            <div className="mt-4 flex flex-wrap items-center justify-between gap-2 text-xs text-muted-foreground">
              <div className="flex items-center gap-4">
                <span className="flex items-center gap-1.5"><i className="h-0.5 w-4 rounded" style={{ background: CHART_HISTORY }} /> Historis</span>
                <span className="flex items-center gap-1.5"><i className="h-0 w-4 border-t-2 border-dashed" style={{ borderColor: CHART_FORECAST }} /> Proyeksi AI</span>
              </div>
              <span>Indeks ilustratif untuk demonstrasi produk.</span>
            </div>
          </FadeIn>

          <div className="grid gap-4">
            {metrics.map(({ label, value, badge, status }, index) => (
              <FadeIn key={label} delay={index * 0.05} className={cn(CARD, "flex flex-1 flex-col justify-center p-5")}>
                <div className="flex items-start justify-between gap-4">
                  <div className="min-w-0">
                    <p className="text-sm text-muted-foreground">{label}</p>
                    <p className="mt-2 truncate text-2xl font-bold text-foreground">{value}</p>
                  </div>
                  <span className={cn("shrink-0 rounded-full border px-3 py-1 text-xs font-semibold", statusClass(status))}>{badge}</span>
                </div>
              </FadeIn>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}

export function HeatmapSection() {
  const highlights = [
    { region: "Sulawesi Barat", commodity: "Tekanan tertinggi", trend: "+3,3%", status: "watch" as Status },
    { region: "Sulawesi Tengah", commodity: "Tekanan menengah", trend: "+2,3%", status: "watch" as Status },
    { region: "DKI Jakarta", commodity: "Pantauan harga", trend: "+2,1%", status: "stable" as Status },
    { region: "Kalimantan Utara", commodity: "Tren naik", trend: "+2,0%", status: "stable" as Status },
  ];

  return (
    <section id="heatmap" className="px-5 py-20 md:px-8 md:py-28">
      <div className="mx-auto max-w-7xl">
        <SectionHeading
          eyebrow="Peta Tekanan Harga"
          title={
            <>
              Lihat tekanan inflasi <span className="font-serif-accent text-secondary">per wilayah.</span>
            </>
          }
          subtitle="Heatmap nasional mengubah pergerakan pasar lokal yang tersebar menjadi intelijen regional yang bisa dibaca dalam hitungan detik — lengkap dengan ranking provinsi dan deteksi tekanan harga."
        />
        <div className="mt-14 grid gap-5 lg:grid-cols-[1.55fr_0.7fr]">
          <FadeIn>
            <BrowserFrame className="green-glow">
              <Image
                src="/dashboard-heatmap.png"
                alt="Peta tekanan harga pangan Indonesia — heatmap per provinsi dengan ranking dan kategori risiko"
                width={1806}
                height={1012}
                className="w-full"
              />
            </BrowserFrame>
          </FadeIn>

          <FadeIn className={cn(CARD, "rounded-3xl p-6")}>
            <div className="flex items-center justify-between">
              <h3 className="text-xl font-semibold text-foreground">Provinsi Paling Tertekan</h3>
              <span className="rounded-full bg-secondary/10 px-2.5 py-1 text-[11px] font-semibold text-secondary">Live</span>
            </div>
            <div className="mt-6 space-y-3">
              {highlights.map((item, index) => (
                <div key={item.region} className="flex items-center gap-3 rounded-2xl bg-white/[0.035] p-3.5">
                  <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-secondary/15 text-xs font-bold text-secondary">
                    {index + 1}
                  </span>
                  <div className="min-w-0 flex-1">
                    <p className="truncate text-sm font-semibold text-foreground">{item.region}</p>
                    <p className="truncate text-xs text-muted-foreground">{item.commodity}</p>
                  </div>
                  <span className={cn("rounded-full border px-2.5 py-1 text-xs font-semibold", statusClass(item.status))}>
                    {item.trend}
                  </span>
                </div>
              ))}
            </div>
            <div className="mt-6 flex items-center gap-3 rounded-2xl border border-white/8 bg-white/[0.02] p-3.5 text-sm text-muted-foreground">
              <ScanSearch className="h-4 w-4 shrink-0 text-secondary" />
              38 provinsi dipantau · 20 alert aktif terdeteksi
            </div>
            <Button asChild variant="outline" className="mt-4 w-full rounded-full border-white/15 bg-white/5 text-sm text-foreground hover:bg-white/10 hover:text-foreground">
              <Link href="/login">Buka Peta Interaktif <ArrowUpRight className="ml-1.5 h-4 w-4" /></Link>
            </Button>
          </FadeIn>
        </div>
      </div>
    </section>
  );
}

function EcosystemDiagram() {
  const reduceMotion = useReducedMotion();
  // Titik jangkar node satelit dalam viewBox 100×100 (disamakan dengan kartu
  // node di bawah). cx/cy = titik kontrol kurva konektor.
  const nodes = [
    { id: "citizens", label: "Warga", Icon: Users, x: 20, y: 20, cx: 40, cy: 27, pos: "left-[3%] top-[6%]" },
    { id: "tpid", label: "TPID", Icon: Landmark, x: 80, y: 20, cx: 60, cy: 27, pos: "right-[3%] top-[6%]" },
    { id: "msmes", label: "UMKM", Icon: Sprout, x: 20, y: 80, cx: 40, cy: 73, pos: "left-[3%] bottom-[6%]" },
    { id: "finance", label: "Keuangan", Icon: Building2, x: 80, y: 80, cx: 60, cy: 73, pos: "right-[3%] bottom-[6%]" },
  ] as const;

  return (
    <div className="relative aspect-square w-full overflow-hidden rounded-3xl border border-white/10 bg-[radial-gradient(circle_at_center,hsl(var(--primary)/0.14),transparent_68%)] p-2">
      <div aria-hidden className="absolute inset-0 rice-texture opacity-[0.12]" />

      {/* Sapuan radar berputar (transform murah, dilewati saat reduced-motion) */}
      {!reduceMotion && (
        <div
          aria-hidden
          className="absolute -inset-1/4 animate-[spin_16s_linear_infinite] bg-[conic-gradient(from_0deg,transparent_0deg,transparent_290deg,hsl(var(--secondary)/0.10)_350deg,transparent_360deg)]"
        />
      )}

      {/* Lapisan konektor + cincin radar */}
      <svg
        className="absolute inset-0 h-full w-full"
        viewBox="0 0 100 100"
        preserveAspectRatio="none"
        aria-hidden
      >
        <defs>
          <linearGradient id="ecoLine" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0%" stopColor="hsl(var(--primary))" stopOpacity={0.2} />
            <stop offset="50%" stopColor="hsl(var(--secondary))" stopOpacity={0.65} />
            <stop offset="100%" stopColor="hsl(var(--primary))" stopOpacity={0.2} />
          </linearGradient>
        </defs>

        {/* Cincin konsentris di sekeliling hub */}
        {[13, 22, 32].map((r, i) => (
          <circle
            key={r}
            cx={50}
            cy={50}
            r={r}
            fill="none"
            stroke={i === 1 ? "hsl(var(--secondary) / 0.20)" : "hsl(var(--foreground) / 0.08)"}
            strokeWidth={0.35}
            strokeDasharray={i === 2 ? "1.5 2.5" : undefined}
          />
        ))}

        {nodes.map(({ id, x, y, cx, cy }, i) => {
          const pathIn = `M${x},${y} Q${cx},${cy} 50,50`;
          const pathOut = `M50,50 Q${cx},${cy} ${x},${y}`;
          return (
            <g key={id}>
              {/* Konektor melengkung: garis dasar + overlay gradien */}
              <path d={pathIn} fill="none" stroke="hsl(var(--foreground) / 0.10)" strokeWidth={0.5} />
              <path d={pathIn} fill="none" stroke="url(#ecoLine)" strokeWidth={0.8} strokeDasharray="3 4" />

              {/* Partikel data: emas mengalir masuk ke hub, hijau keluar ke node */}
              {!reduceMotion && (
                <>
                  <circle r={1.1} fill="hsl(var(--secondary))">
                    <animateMotion dur="3.4s" begin={`${i * 0.85}s`} repeatCount="indefinite" path={pathIn} />
                  </circle>
                  <circle r={0.8} fill="hsl(var(--primary))" opacity={0.9}>
                    <animateMotion dur="4.2s" begin={`${1.6 + i * 0.85}s`} repeatCount="indefinite" path={pathOut} />
                  </circle>
                </>
              )}
            </g>
          );
        })}
      </svg>

      {/* Hub tengah */}
      <div className="absolute left-1/2 top-1/2 z-10 -translate-x-1/2 -translate-y-1/2">
        {!reduceMotion && (
          <>
            <motion.span
              className="absolute inset-0 -z-10 rounded-full border border-secondary/35"
              animate={{ scale: [1, 1.9], opacity: [0.55, 0] }}
              transition={{ duration: 2.8, repeat: Infinity, ease: "easeOut" }}
            />
            <motion.span
              className="absolute inset-0 -z-10 rounded-full border border-secondary/25"
              animate={{ scale: [1, 2.3], opacity: [0.4, 0] }}
              transition={{ duration: 2.8, repeat: Infinity, ease: "easeOut", delay: 1.4 }}
            />
          </>
        )}
        <div className="relative flex h-28 w-28 flex-col items-center justify-center gap-1 rounded-full border border-secondary/50 bg-[radial-gradient(circle_at_32%_26%,hsl(var(--secondary)/0.38),hsl(var(--secondary)/0.10)_72%)] text-secondary shadow-[0_0_70px_-10px_hsl(var(--secondary)/0.85)]">
          {/* Cincin dalam putus-putus yang berputar pelan */}
          <span
            aria-hidden
            className={cn(
              "absolute inset-1.5 rounded-full border border-dashed border-secondary/40",
              !reduceMotion && "animate-[spin_26s_linear_infinite]",
            )}
          />
          <Wheat className="h-10 w-10 drop-shadow-[0_0_10px_hsl(var(--secondary)/0.7)]" />
          <span className="text-[9px] font-bold uppercase tracking-[0.18em]">Sinyal</span>
        </div>
      </div>

      {/* Node satelit */}
      {nodes.map(({ id, label, Icon, pos }) => (
        <div
          key={id}
          className={cn(
            "absolute z-10 flex items-center gap-2 rounded-2xl border border-secondary/20 bg-background/95 px-3 py-2.5 shadow-[0_10px_30px_-8px_rgba(0,0,0,0.6),0_0_20px_-6px_hsl(var(--secondary)/0.35)]",
            pos,
          )}
        >
          <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-secondary/15 text-secondary">
            <Icon className="h-4 w-4" />
          </span>
          <span className="text-sm font-semibold text-foreground">{label}</span>
        </div>
      ))}

      {/* Keterangan */}
      <div className="absolute inset-x-0 bottom-3 z-10 text-center">
        <p className="text-[11px] text-muted-foreground">
          Satu sinyal tervalidasi — dibagikan ke seluruh ekosistem
        </p>
      </div>
    </div>
  );
}

export function EcosystemSection() {
  const cards = [
    [Users, "Warga", "Bandingkan harga sebelum ke pasar dan terima notifikasi perubahan harga."],
    [Landmark, "Pemerintah Daerah", "Deteksi tekanan inflasi regional lebih awal dan dukung pengambilan keputusan TPID."],
    [Sprout, "Petani & UMKM", "Pahami permintaan, pergerakan harga, dan peluang pasokan antarwilayah."],
    [Building2, "Institusi Keuangan", "Manfaatkan sinyal harga pangan agregat untuk asuransi parametrik, pemodelan risiko, dan kredit pertanian."],
  ] as const;

  return (
    <section id="ecosystem" className="px-5 py-20 md:px-8 md:py-28">
      <div className="mx-auto max-w-7xl">
        <SectionHeading
          eyebrow="Ekosistem"
          title="Dibangun untuk seluruh ekosistem ketahanan pangan."
          subtitle="Intelijen harga pangan makin bernilai ketika warga, institusi, dan pelaku rantai pasok membaca sinyal tervalidasi yang sama."
        />
        <div className="mt-14 grid gap-8 lg:grid-cols-[1fr_0.8fr] lg:items-center">
          <div className="grid gap-4 md:grid-cols-2">
            {cards.map(([Icon, title, copy], index) => (
              <FadeIn key={title} delay={index * 0.06} className={cn(CARD, "rounded-3xl p-8 transition hover:border-secondary/30")}>
                <span className="inline-flex h-12 w-12 items-center justify-center rounded-xl bg-secondary/12 text-secondary">
                  <Icon className="h-6 w-6" />
                </span>
                <h3 className="mt-6 text-xl font-semibold text-foreground">{title}</h3>
                <p className="mt-3 text-sm leading-6 text-muted-foreground">{copy}</p>
              </FadeIn>
            ))}
          </div>
          <FadeIn>
            <EcosystemDiagram />
          </FadeIn>
        </div>
      </div>
    </section>
  );
}

export function GamificationSection() {
  const levels = [
    ["Pemantau Pemula", "0–500 poin", 18],
    ["Pengamat Aktif", "501–2.000 poin", 42],
    ["Sentinel Harga", "2.001–10.000 poin", 74],
    ["Pahlawan Pangan", "10.000+ poin", 94],
  ] as const;
  const activities = ["+10 Lapor harga komoditas", "+5 Verifikasi data orang lain", "+25 Streak 7 hari", "+50 Challenge mingguan", "+30 Ajak kontributor baru"];

  return (
    <section className="px-5 py-20 md:px-8 md:py-28">
      <div className="mx-auto max-w-7xl">
        <SectionHeading
          eyebrow="Komunitas"
          title="Data komunitas yang terus membaik."
          subtitle="Gamifikasi menjaga partisipasi pelapor tetap hidup tanpa bergantung hanya pada insentif tunai."
        />
        <div className="mt-14 grid gap-5 lg:grid-cols-[1.1fr_0.9fr]">
          <div className="grid gap-4 md:grid-cols-2">
            {levels.map(([title, range, progress], index) => (
              <FadeIn key={title} delay={index * 0.05} className={cn(CARD, "rounded-3xl p-6")}>
                <div className="flex items-center justify-between">
                  <Trophy className="h-7 w-7 text-secondary" />
                  <span className="rounded-full bg-secondary/10 px-3 py-1 text-xs font-semibold text-secondary">{range}</span>
                </div>
                <h3 className="mt-6 text-xl font-semibold text-foreground">{title}</h3>
                <div className="mt-5 h-2 rounded-full bg-white/10">
                  <div className="h-full rounded-full bg-gradient-to-r from-primary to-secondary" style={{ width: `${progress}%` }} />
                </div>
              </FadeIn>
            ))}
          </div>
          <FadeIn className={cn(CARD, "rounded-3xl p-7")}>
            <h3 className="text-xl font-semibold text-foreground">Aktivitas Poin</h3>
            <div className="mt-6 space-y-3">
              {activities.map((activity) => (
                <div key={activity} className="flex items-center gap-3 rounded-2xl bg-white/[0.035] p-4 text-sm text-muted-foreground">
                  <BadgeCheck className="h-5 w-5 shrink-0 text-secondary" />
                  {activity}
                </div>
              ))}
            </div>
          </FadeIn>
        </div>
      </div>
    </section>
  );
}

export function FaqSection() {
  const faqs = [
    [
      "Dari mana data harga inflasi.id berasal?",
      "Data dikumpulkan dari laporan warga di lapangan (foto struk, harga, dan lokasi pasar), data pasar publik, serta referensi resmi. Semua sinyal dinormalisasi per wilayah sebelum masuk dashboard.",
    ],
    [
      "Bagaimana keandalan data dijaga?",
      "Setiap laporan melewati validasi berlapis: geofencing GPS, peer review antarkontributor, dan deteksi anomali berbasis AI yang menyaring data tidak wajar sebelum diagregasi.",
    ],
    [
      "Apakah inflasi.id gratis?",
      "Ya, dashboard publik dapat diakses gratis oleh warga. Untuk kebutuhan institusi — TPID, fintech, asuransi, atau riset — tersedia solusi khusus melalui halaman kemitraan.",
    ],
    [
      "Wilayah mana saja yang dicakup?",
      "Saat ini 38 provinsi terpantau melalui heatmap nasional, dengan ranking provinsi dan peringatan tekanan harga yang diperbarui secara real-time.",
    ],
    [
      "Bagaimana cara ikut melapor harga?",
      "Masuk ke dashboard, pilih menu lapor harga, lalu unggah foto dan harga komoditas dari pasar terdekat. Kontribusi tervalidasi mendapat poin dan naik level di leaderboard komunitas.",
    ],
  ] as const;

  return (
    <section className="px-5 py-20 md:px-8 md:py-28">
      <div className="mx-auto max-w-3xl">
        <SectionHeading
          eyebrow="FAQ"
          title="Pertanyaan yang sering diajukan."
          subtitle="Hal-hal yang paling sering ditanyakan warga dan institusi sebelum mulai memakai inflasi.id."
        />
        <div className="mt-12 space-y-3">
          {faqs.map(([question, answer], index) => (
            <FadeIn key={question} delay={index * 0.04}>
              <details className={cn(CARD, "group overflow-hidden")}>
                <summary className="flex cursor-pointer list-none items-center justify-between gap-4 px-6 py-5 text-left text-base font-semibold text-foreground transition hover:bg-white/[0.02] [&::-webkit-details-marker]:hidden">
                  {question}
                  <ChevronDown className="h-5 w-5 shrink-0 text-muted-foreground transition-transform group-open:rotate-180" />
                </summary>
                <p className="px-6 pb-6 text-sm leading-7 text-muted-foreground">{answer}</p>
              </details>
            </FadeIn>
          ))}
        </div>
      </div>
    </section>
  );
}

export function CTASection() {
  return (
    <section className="relative flex min-h-[70vh] items-center justify-center overflow-hidden px-5 py-24 text-center md:px-8">
      <div aria-hidden className="absolute inset-0 bg-[radial-gradient(circle_at_center,hsl(var(--primary)/0.26),transparent_58%)]" />
      <div aria-hidden className="absolute inset-0 rice-texture opacity-20" />
      <FadeIn className="relative z-10 mx-auto max-w-5xl">
        <h2 className="text-balance text-4xl font-medium leading-tight tracking-[-1.4px] text-foreground md:text-7xl">
          Ketahanan pangan dimulai dari <span className="font-serif-accent text-secondary">data yang transparan.</span>
        </h2>
        <p className="mx-auto mt-6 max-w-2xl text-lg leading-8 text-muted-foreground">
          Dibangun untuk Indonesia. Ditenagai komunitas, data tervalidasi, dan AI.
        </p>
        <div className="mt-9 flex flex-col items-center justify-center gap-3 sm:flex-row">
          <Button asChild className="h-12 rounded-full bg-secondary px-8 text-base font-semibold text-secondary-foreground hover:bg-secondary/90">
            <Link href="/login">Buka Dashboard</Link>
          </Button>
          <Button asChild variant="outline" className="h-12 rounded-full border-white/15 bg-white/5 px-8 text-base text-foreground hover:bg-white/10 hover:text-foreground">
            <Link href="/partner">Jadi Mitra Kami</Link>
          </Button>
        </div>
        <p className="mt-8 text-sm text-muted-foreground">Dirancang untuk warga, pemerintah daerah, peneliti, dan institusi keuangan.</p>
      </FadeIn>
    </section>
  );
}

export function Footer() {
  const columns = [
    ["Platform", "Blog", "Dashboard", "Peta Harga", "Prediksi AI"],
    ["Data", "Metodologi", "Validasi", "Cakupan"],
    ["Ekosistem", "Pemerintah", "Fintech", "Asuransi", "Riset"],
    ["Perusahaan", "Tentang Kami", "Kontak", "Kemitraan"],
  ];
  // Tautan yang punya tujuan nyata; selain ini anchor placeholder.
  const hrefs: Record<string, string> = {
    // Platform
    Blog: "/blog",
    Dashboard: "/welcome#dashboard",
    "Peta Harga": "/welcome#heatmap",
    "Prediksi AI": "/welcome#forecasting",
    // Data
    Metodologi: "/methodology",
    Validasi: "/methodology#validation",
    Cakupan: "/methodology#coverage",
    // Ekosistem
    Pemerintah: "/solutions#government",
    Fintech: "/solutions#fintech",
    Asuransi: "/solutions#insurance",
    Riset: "/solutions#research",
    // Perusahaan
    "Tentang Kami": "/about",
    Kontak: "/contact",
    Kemitraan: "/partner",
  };

  return (
    <footer className="border-t border-white/10 px-5 py-12 md:px-8">
      <div className="mx-auto max-w-7xl">
        <div className="grid gap-10 md:grid-cols-[1.4fr_repeat(4,1fr)]">
          <div>
            <Link href="/welcome" className="flex items-center gap-3">
              <Image src="/logo.svg" alt="INFLASI ID" width={40} height={40} className="h-10 w-10 rounded-full" />
              <span className="text-xl font-bold tracking-tight text-foreground">inflasi.id</span>
            </Link>
            <p className="mt-3 max-w-xs text-sm leading-6 text-muted-foreground">
              Platform intelijen inflasi pangan untuk Indonesia — data komunitas tervalidasi, heatmap nasional, dan prediksi AI.
            </p>
          </div>
          {columns.map(([title, ...links]) => (
            <div key={title}>
              <p className="mb-4 text-sm font-semibold text-foreground">{title}</p>
              <div className="space-y-3">
                {links.map((link) => (
                  <Link key={link} href={hrefs[link] ?? "#"} className="block text-sm text-muted-foreground transition hover:text-foreground">
                    {link}
                  </Link>
                ))}
              </div>
            </div>
          ))}
        </div>
        <p className="mt-12 border-t border-white/10 pt-6 text-xs text-muted-foreground">© 2026 inflasi.id — Platform Intelijen Inflasi Pangan Indonesia.</p>
      </div>
    </footer>
  );
}

export default function PremiumLandingPage() {
  return (
    <main className="landing-theme min-h-screen overflow-hidden bg-background text-foreground">
      <Navbar />
      <Hero />
      <ProblemSection />
      <HowItWorks />
      <ForecastingSection />
      <HeatmapSection />
      <EcosystemSection />
      <GamificationSection />
      <FaqSection />
      <CTASection />
      <Footer />
    </main>
  );
}
