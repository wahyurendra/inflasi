"use client";

import { ReactNode, useRef, useState } from "react";
import Image from "next/image";
import Link from "next/link";
import { motion, useReducedMotion, useScroll, useTransform, type MotionValue } from "framer-motion";
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
  BadgeCheck,
  Bell,
  Building2,
  Camera,
  Landmark,
  LineChart as LineChartIcon,
  MapPin,
  ScanSearch,
  ShieldCheck,
  Sprout,
  Trophy,
  Users,
  Wheat,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

type Status = "stable" | "watch" | "spike";

const navLinks = [
  { label: "Dashboard", href: "/welcome#dashboard" },
  { label: "Heatmap", href: "/welcome#heatmap" },
  { label: "Forecasting", href: "/welcome#forecasting" },
  { label: "Ecosystem", href: "/welcome#ecosystem" },
  { label: "Blog", href: "/blog" },
];

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
      { month: "May", history: 124, forecast: 124 },
      { month: "Jun", history: null, forecast: 133 },
      { month: "Jul", history: null, forecast: 141 },
      { month: "Aug", history: null, forecast: 148 },
    ],
    oneMonth: { value: "+7.3%", badge: "Watch", status: "watch" },
    threeMonth: { value: "+19.4%", badge: "High Risk", status: "spike" },
    confidence: { value: "91%", badge: "Validated", status: "stable" },
    anomaly: { value: "Papua — lonjakan", badge: "Spike", status: "spike" },
  },
  Beras: {
    name: "Beras",
    series: [
      { month: "Jan", history: 100, forecast: null },
      { month: "Feb", history: 100, forecast: null },
      { month: "Mar", history: 101, forecast: null },
      { month: "Apr", history: 101, forecast: null },
      { month: "May", history: 102, forecast: 102 },
      { month: "Jun", history: null, forecast: 102 },
      { month: "Jul", history: null, forecast: 103 },
      { month: "Aug", history: null, forecast: 103 },
    ],
    oneMonth: { value: "+0.4%", badge: "Stabil", status: "stable" },
    threeMonth: { value: "+1.1%", badge: "Stabil", status: "stable" },
    confidence: { value: "94%", badge: "Validated", status: "stable" },
    anomaly: { value: "Tidak terdeteksi", badge: "Aman", status: "stable" },
  },
  Telur: {
    name: "Telur Ayam",
    series: [
      { month: "Jan", history: 100, forecast: null },
      { month: "Feb", history: 102, forecast: null },
      { month: "Mar", history: 105, forecast: null },
      { month: "Apr", history: 107, forecast: null },
      { month: "May", history: 110, forecast: 110 },
      { month: "Jun", history: null, forecast: 114 },
      { month: "Jul", history: null, forecast: 117 },
      { month: "Aug", history: null, forecast: 120 },
    ],
    oneMonth: { value: "+3.4%", badge: "Watch", status: "watch" },
    threeMonth: { value: "+9.1%", badge: "Watch", status: "watch" },
    confidence: { value: "88%", badge: "Validated", status: "stable" },
    anomaly: { value: "Sulsel — naik", badge: "Watch", status: "watch" },
  },
  "Minyak Goreng": {
    name: "Minyak Goreng",
    series: [
      { month: "Jan", history: 100, forecast: null },
      { month: "Feb", history: 101, forecast: null },
      { month: "Mar", history: 103, forecast: null },
      { month: "Apr", history: 106, forecast: null },
      { month: "May", history: 109, forecast: 109 },
      { month: "Jun", history: null, forecast: 113 },
      { month: "Jul", history: null, forecast: 116 },
      { month: "Aug", history: null, forecast: 118 },
    ],
    oneMonth: { value: "+2.8%", badge: "Watch", status: "watch" },
    threeMonth: { value: "+8.3%", badge: "Watch", status: "watch" },
    confidence: { value: "86%", badge: "Validated", status: "stable" },
    anomaly: { value: "Sumut — pantau", badge: "Watch", status: "watch" },
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
  accent,
  subtitle,
  className,
}: {
  eyebrow?: string;
  title: ReactNode;
  accent?: ReactNode;
  subtitle: string;
  className?: string;
}) {
  return (
    <FadeIn className={cn("mx-auto max-w-4xl text-center", className)}>
      {eyebrow && (
        <p className="mb-4 text-sm font-semibold uppercase tracking-[0.24em] text-secondary/90">
          {eyebrow}
        </p>
      )}
      <h2 className="text-balance text-4xl font-medium leading-tight tracking-[-1.4px] text-foreground md:text-6xl">
        {title} {accent}
      </h2>
      <p className="mx-auto mt-5 max-w-3xl text-base leading-7 text-muted-foreground md:text-lg">
        {subtitle}
      </p>
    </FadeIn>
  );
}

export function Navbar() {
  return (
    <nav className="fixed inset-x-0 top-0 z-50 border-b border-white/5 bg-background/70 px-5 py-4 backdrop-blur-xl md:px-28">
      <div className="mx-auto flex max-w-7xl items-center justify-between gap-6">
        <Link href="/welcome" className="flex items-center gap-3">
          <Image src="/logo.svg" alt="INFLASI ID" width={40} height={40} priority className="h-10 w-10 rounded-full" />
          <span className="text-xl font-bold tracking-tight text-foreground">inflasi.id</span>
          <span className="hidden rounded-full border border-white/10 px-2 py-1 text-xs text-muted-foreground md:inline">
            Food Intelligence
          </span>
        </Link>

        <div className="hidden items-center gap-1 md:flex">
          {navLinks.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              className="rounded-full px-4 py-2 text-sm text-muted-foreground transition hover:bg-white/5 hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
            >
              {link.label}
            </Link>
          ))}
        </div>

        <div className="flex items-center gap-3">
          <Link href="#ecosystem" className="hidden text-sm text-muted-foreground transition hover:text-foreground lg:inline">
            Partner with us
          </Link>
          <Button asChild className="rounded-full bg-secondary px-5 py-2.5 text-sm font-semibold text-secondary-foreground hover:bg-secondary/90">
            <Link href="/login">Open Dashboard</Link>
          </Button>
        </div>
      </div>
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
    <div className={cn("liquid-glass rounded-2xl px-5 py-4 text-left", highlighted && "gold-glow")}>
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
        "overflow-hidden rounded-2xl border border-white/12 bg-[#0e1512] shadow-[0_40px_120px_-24px_rgba(0,0,0,0.65)]",
        className,
      )}
    >
      {/* Browser chrome */}
      <div className="flex items-center gap-3 border-b border-white/8 bg-white/[0.03] px-4 py-3">
        <div className="flex items-center gap-1.5">
          <span className="h-3 w-3 rounded-full bg-[#ff5f57]" />
          <span className="h-3 w-3 rounded-full bg-[#febc2e]" />
          <span className="h-3 w-3 rounded-full bg-[#28c840]" />
        </div>
        <div className="mx-auto flex max-w-sm flex-1 items-center justify-center gap-2 rounded-md border border-white/8 bg-black/30 px-3 py-1.5">
          <ShieldCheck className="h-3 w-3 text-success" />
          <span className="truncate text-[11px] text-muted-foreground">{url}</span>
        </div>
        <span className="hidden items-center gap-1.5 rounded-full border border-success/25 bg-success/10 px-2.5 py-1 text-[10px] font-semibold text-success sm:inline-flex">
          <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-success" />
          Live
        </span>
      </div>
      {children}
    </div>
  );
}

export function DashboardPreview() {
  return (
    <div id="dashboard" className="relative mx-auto w-[94%] max-w-6xl">
      {/* Ambient glow behind the product shot */}
      <div
        aria-hidden
        className="pointer-events-none absolute -inset-x-10 -top-10 bottom-0 bg-[radial-gradient(ellipse_at_center,hsl(var(--primary)/0.22),transparent_60%)] blur-2xl"
      />

      <BrowserFrame className="relative green-glow">
        <Image
          src="/dashboard-heatmap.png"
          alt="Dashboard Peta Tekanan Harga inflasi.id — heatmap nasional, ranking provinsi, dan deteksi tekanan harga pangan secara real-time"
          width={1806}
          height={1012}
          priority
          className="w-full"
        />
      </BrowserFrame>

      {/* Floating stat chips for that polished product-shot feel */}
      <div className="pointer-events-none absolute -left-4 top-20 hidden rounded-2xl border border-white/10 bg-background/85 px-4 py-3 shadow-2xl backdrop-blur-md md:block">
        <p className="text-[10px] uppercase tracking-[0.18em] text-secondary">Cakupan</p>
        <p className="mt-1 text-xl font-bold text-foreground">38 Provinsi</p>
        <p className="text-[11px] text-muted-foreground">Heatmap live</p>
      </div>
      <div className="pointer-events-none absolute -right-4 bottom-24 hidden rounded-2xl border border-white/10 bg-background/85 px-4 py-3 shadow-2xl backdrop-blur-md md:block">
        <div className="flex items-center gap-2">
          <Bell className="h-4 w-4 text-warning" />
          <p className="text-[10px] uppercase tracking-[0.18em] text-warning">Alert Aktif</p>
        </div>
        <p className="mt-1 text-xl font-bold text-foreground">20 Sinyal</p>
        <p className="text-[11px] text-muted-foreground">Real-time monitoring</p>
      </div>
    </div>
  );
}

function AnimatedHeroBackground({
  glowScale,
  glowOpacity,
}: {
  glowScale: MotionValue<number>;
  glowOpacity: MotionValue<number>;
}) {
  const reduceMotion = useReducedMotion();

  // Drifting aurora blobs. Each gets a slightly different size, hue, position,
  // and animation timing so the field never visibly loops.
  const blobs = [
    { className: "left-[8%] top-[6%] h-[42vw] w-[42vw] bg-[radial-gradient(circle,hsl(var(--primary)/0.30),transparent_60%)]", duration: 16, delay: 0 },
    { className: "right-[4%] top-[18%] h-[36vw] w-[36vw] bg-[radial-gradient(circle,hsl(var(--secondary)/0.16),transparent_62%)]", duration: 21, delay: 1.5 },
    { className: "left-[28%] top-[40%] h-[34vw] w-[34vw] bg-[radial-gradient(circle,hsl(var(--primary)/0.18),transparent_64%)]", duration: 19, delay: 3 },
  ];

  return (
    <div aria-hidden className="pointer-events-none absolute inset-0 overflow-hidden">
      {/* Base wash so blobs read against the dark ground */}
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_50%_-10%,hsl(var(--primary)/0.10),transparent_55%)]" />

      {/* Drifting aurora field */}
      <div className="absolute inset-0 blur-[60px]">
        {blobs.map((b, i) => (
          <span
            key={i}
            className={cn("absolute rounded-full will-change-transform", b.className)}
            style={
              reduceMotion
                ? undefined
                : { animation: `aurora-drift ${b.duration}s ease-in-out ${b.delay}s infinite` }
            }
          />
        ))}
      </div>

      {/* Panning technical grid */}
      <div className="absolute inset-0 landing-grid opacity-70" />

      {/* Parallax top spotlight (driven by scroll) */}
      <motion.div
        style={{ scale: glowScale, opacity: glowOpacity }}
        className="absolute inset-x-0 top-0 h-[620px] bg-[radial-gradient(circle_at_50%_0%,hsl(var(--primary)/0.30),transparent_62%)]"
      />

      {/* Sweeping light beam */}
      {!reduceMotion && (
        <motion.div
          className="absolute -inset-x-1/4 top-0 h-[520px] bg-[linear-gradient(105deg,transparent_40%,hsl(var(--secondary)/0.06)_50%,transparent_60%)]"
          animate={{ x: ["-12%", "12%", "-12%"] }}
          transition={{ duration: 14, ease: "easeInOut", repeat: Infinity }}
        />
      )}

      {/* Fine grain + edge vignette + bottom fade to page */}
      <div className="absolute inset-0 opacity-30 landing-grain" />
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,transparent_55%,hsl(var(--background)/0.85)_100%)]" />
      <div className="absolute inset-x-0 bottom-0 h-48 bg-gradient-to-b from-transparent to-background" />
    </div>
  );
}

export function Hero() {
  const sectionRef = useRef<HTMLElement>(null);
  const reduceMotion = useReducedMotion();
  const { scrollYProgress } = useScroll({ target: sectionRef, offset: ["start start", "end start"] });
  const textY = useTransform(scrollYProgress, [0, 1], reduceMotion ? [0, 0] : [0, -200]);
  const textOpacity = useTransform(scrollYProgress, [0, 0.7], [1, reduceMotion ? 1 : 0]);
  const dashboardY = useTransform(scrollYProgress, [0, 1], reduceMotion ? [0, 0] : [0, -250]);
  const glowScale = useTransform(scrollYProgress, [0, 1], reduceMotion ? [1, 1] : [1, 1.08]);
  const glowOpacity = useTransform(scrollYProgress, [0, 1], [0.8, 0.4]);

  return (
    <section ref={sectionRef} className="relative min-h-screen overflow-hidden px-4 pb-24 pt-32 md:pt-36">
      <AnimatedHeroBackground glowScale={glowScale} glowOpacity={glowOpacity} />

      <motion.div style={{ y: textY, opacity: textOpacity }} className="relative z-10 mx-auto max-w-6xl text-center">
        <motion.div
          initial={reduceMotion ? false : { opacity: 0, y: 10 }}
          animate={reduceMotion ? undefined : { opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="liquid-glass mb-6 inline-flex items-center gap-3 rounded-full px-4 py-2 text-sm text-muted-foreground"
        >
          <span className="rounded-md bg-destructive px-2 py-1 text-xs font-semibold text-white">LIVE</span>
          Real-time food price intelligence across Indonesia
        </motion.div>

        <motion.h1
          initial={reduceMotion ? false : { opacity: 0, y: 20 }}
          animate={reduceMotion ? undefined : { opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.1 }}
          className="text-balance text-5xl font-medium leading-[1.05] tracking-[-2.5px] text-foreground md:text-7xl lg:text-8xl"
        >
          Indonesia&apos;s Food
          <br />
          Inflation <span className="font-serif-accent text-secondary">Intelligence.</span>
        </motion.h1>

        <motion.p
          initial={reduceMotion ? false : { opacity: 0, y: 20 }}
          animate={reduceMotion ? undefined : { opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.2 }}
          className="mx-auto mt-6 max-w-3xl text-base leading-7 text-hero-subtitle opacity-90 md:text-lg"
        >
          inflasi.id helps citizens, local governments, and financial institutions monitor food prices, detect anomalies, and forecast inflation trends using crowdsourced intelligence and AI.
        </motion.p>

        <motion.div
          initial={reduceMotion ? false : { opacity: 0, y: 20 }}
          animate={reduceMotion ? undefined : { opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.3 }}
          className="mt-8 flex flex-col items-center justify-center gap-3 sm:flex-row"
        >
          <motion.div whileHover={reduceMotion ? undefined : { scale: 1.03 }} whileTap={reduceMotion ? undefined : { scale: 0.98 }}>
            <Button asChild className="h-12 rounded-full bg-secondary px-8 text-base font-semibold text-secondary-foreground hover:bg-secondary/90">
              <Link href="/login">Explore Dashboard <ArrowRight className="ml-2 h-4 w-4" /></Link>
            </Button>
          </motion.div>
          <Button asChild variant="outline" className="h-12 rounded-full border-white/15 bg-white/5 px-8 text-base font-medium text-foreground backdrop-blur hover:bg-white/10 hover:text-foreground">
            <Link href="#heatmap">View National Heatmap</Link>
          </Button>
        </motion.div>

        <motion.div
          initial={reduceMotion ? false : { opacity: 0, y: 24 }}
          animate={reduceMotion ? undefined : { opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.35 }}
          className="mx-auto mt-10 grid max-w-3xl grid-cols-2 gap-3 md:grid-cols-4"
        >
          <MetricCard value="38" label="Provinsi Terpantau" />
          <MetricCard value="10+" label="Komoditas Strategis" highlighted />
          <MetricCard value="24/7" label="Data Feed Real-time" />
          <MetricCard value="AI" label="Forecasting Aktif" />
        </motion.div>
      </motion.div>

      <motion.div
        style={{ y: dashboardY }}
        initial={reduceMotion ? false : { opacity: 0, y: 40 }}
        animate={reduceMotion ? undefined : { opacity: 1, y: 0 }}
        transition={{ duration: 0.8, delay: 0.4 }}
        className="relative z-10 mx-auto mt-14 w-full max-w-6xl md:mt-20"
      >
        <DashboardPreview />
      </motion.div>
    </section>
  );
}

export function ProblemSection() {
  return (
    <section id="problem" className="bg-background px-8 py-24 md:px-28 md:py-32">
      <div className="mx-auto max-w-7xl">
        <FadeIn className="max-w-4xl">
          <h2 className="text-balance text-4xl font-medium leading-tight tracking-[-1.4px] text-foreground md:text-6xl">
            Indonesia still lacks <span className="font-serif-accent text-secondary">real-time</span> food price visibility.
          </h2>
          <p className="mt-5 max-w-3xl text-lg leading-8 text-muted-foreground">
            Food prices can move faster than official reporting cycles. inflasi.id fills the visibility gap with community-powered data, validation, and forecasting.
          </p>
        </FadeIn>

        <div className="mt-12 grid gap-4 md:grid-cols-3">
          {[
            ["84%", "Wilayah belum memiliki data harga harian"],
            ["432", "Kabupaten/kota di luar jangkauan pemantauan harian"],
            ["0", "Data akhir pekan & hari libur dari sistem tradisional"],
          ].map(([value, label], index) => (
            <FadeIn key={value} delay={index * 0.08} className="liquid-glass rounded-3xl p-7">
              <p className="text-5xl font-bold text-foreground">{value}</p>
              <p className="mt-4 text-sm leading-6 text-muted-foreground">{label}</p>
            </FadeIn>
          ))}
        </div>

        <FadeIn className="liquid-glass gold-glow mt-10 rounded-3xl p-6 md:p-8">
          <div className="mb-8 flex flex-col justify-between gap-4 md:flex-row md:items-end">
            <div>
              <h3 className="text-2xl font-semibold text-foreground">Same commodity. Different reality.</h3>
              <p className="mt-2 max-w-2xl text-sm leading-6 text-muted-foreground">
                Real-time visibility reveals price distance before it becomes a policy blind spot.
              </p>
            </div>
            <span className="rounded-full border border-secondary/25 bg-secondary/10 px-4 py-2 text-sm font-semibold text-secondary">Cabai Merah</span>
          </div>
          <div className="grid gap-6 md:grid-cols-[1fr_1.2fr_1fr] md:items-center">
            <ComparisonCard region="Papua" price="Rp200.000/kg" status="Extreme Spike" tone="spike" />
            <div className="relative h-20">
              <div className="absolute left-4 right-4 top-1/2 h-1 -translate-y-1/2 rounded-full bg-gradient-to-r from-success via-warning to-danger" />
              <span className="absolute left-3 top-1/2 h-5 w-5 -translate-y-1/2 rounded-full border-4 border-background bg-success" />
              <span className="absolute right-3 top-1/2 h-5 w-5 -translate-y-1/2 rounded-full border-4 border-background bg-danger" />
              <p className="absolute inset-x-0 bottom-0 text-center text-xs text-muted-foreground">185k rupiah/kg regional spread</p>
            </div>
            <ComparisonCard region="Brebes" price="Rp15.000/kg" status="Stable Supply" tone="stable" />
          </div>
        </FadeIn>
      </div>
    </section>
  );
}

function ComparisonCard({ region, price, status, tone }: { region: string; price: string; status: string; tone: Status }) {
  return (
    <div className="rounded-2xl border border-white/10 bg-white/[0.035] p-5">
      <p className="text-sm text-muted-foreground">{region}</p>
      <p className="mt-2 text-lg font-semibold text-foreground">Cabai Merah</p>
      <p className="mt-4 text-3xl font-bold text-foreground">{price}</p>
      <span className={cn("mt-4 inline-flex rounded-full border px-3 py-1 text-xs font-semibold", statusClass(tone))}>{status}</span>
    </div>
  );
}

export function HowItWorks() {
  const steps = [
    [Camera, "Citizens report prices", "Foto struk, harga komoditas, dan lokasi pasar dalam hitungan detik."],
    [MapPin, "GPS & AI validation", "Geofencing, peer review, dan anomaly detection menyaring data tidak wajar."],
    [ShieldCheck, "Data aggregation", "Data publik, crowdsource, dan referensi resmi dinormalisasi per wilayah."],
    [LineChartIcon, "Inflation forecasting", "Model AI membaca tren, risiko lonjakan, dan proyeksi 1-3 bulan."],
    [Bell, "Dashboard & alerts", "Pemerintah, masyarakat, dan institusi mendapat early warning real-time."],
  ] as const;

  return (
    <section className="px-8 py-24 md:px-28 md:py-32">
      <div className="mx-auto max-w-7xl">
        <SectionHeading
          eyebrow="Signal Pipeline"
          title="From market reports to national intelligence."
          subtitle="Every citizen report becomes part of a validated food price signal."
        />
        <div className="mt-14 grid gap-4 lg:grid-cols-5">
          {steps.map(([Icon, title, description], index) => (
            <FadeIn key={title} delay={index * 0.06} className="liquid-glass rounded-2xl p-6 transition hover:green-glow">
              <div className="mb-6 flex items-center justify-between">
                <Icon className="h-7 w-7 text-secondary" />
                <span className="text-sm font-semibold text-secondary">0{index + 1}</span>
              </div>
              <h3 className="text-lg font-semibold text-foreground">{title}</h3>
              <p className="mt-3 text-sm leading-6 text-muted-foreground">{description}</p>
            </FadeIn>
          ))}
        </div>
      </div>
    </section>
  );
}

export function ForecastingSection() {
  const [commodity, setCommodity] = useState<keyof typeof FORECASTS>("Cabai Merah");
  const active = FORECASTS[commodity];

  const metrics: { label: string; value: string; badge: string; status: Status }[] = [
    { label: "Forecast 1 Bulan", value: active.oneMonth.value, badge: active.oneMonth.badge, status: active.oneMonth.status },
    { label: "Forecast 3 Bulan", value: active.threeMonth.value, badge: active.threeMonth.badge, status: active.threeMonth.status },
    { label: "Confidence Model", value: active.confidence.value, badge: active.confidence.badge, status: active.confidence.status },
    { label: "Anomali Terdeteksi", value: active.anomaly.value, badge: active.anomaly.badge, status: active.anomaly.status },
  ];

  return (
    <section id="forecasting" className="relative px-8 py-24 md:px-28 md:py-32">
      <div aria-hidden className="pointer-events-none absolute inset-x-0 top-20 h-80 bg-[radial-gradient(circle,hsl(var(--secondary)/0.10),transparent_62%)]" />
      <div className="relative mx-auto max-w-7xl">
        <SectionHeading
          eyebrow="AI Forecasting"
          title={<>Predict food inflation <span className="font-serif-accent text-secondary">before</span> it becomes a crisis.</>}
          subtitle="inflasi.id memadukan riwayat harga, sinyal regional, laporan crowdsourced, dan deteksi anomali untuk mengidentifikasi tekanan inflasi lebih awal."
        />
        <div className="mt-14 grid items-stretch gap-5 lg:grid-cols-[1.45fr_0.85fr]">
          <FadeIn className="liquid-glass flex flex-col rounded-3xl p-5 md:p-7">
            <div className="mb-5 flex flex-wrap items-center justify-between gap-3">
              <div>
                <p className="text-lg font-semibold text-foreground">Forecast Model</p>
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
                    <stop offset="0%" stopColor="hsl(var(--secondary))" stopOpacity={0.26} />
                    <stop offset="100%" stopColor="hsl(var(--secondary))" stopOpacity={0.02} />
                  </linearGradient>
                </defs>
                <CartesianGrid stroke="hsl(var(--foreground) / 0.08)" vertical={false} />
                <XAxis dataKey="month" tick={{ fill: "hsl(var(--muted-foreground))", fontSize: 12 }} tickLine={false} axisLine={false} />
                <YAxis domain={["dataMin - 4", "dataMax + 6"]} tick={{ fill: "hsl(var(--muted-foreground))", fontSize: 12 }} tickLine={false} axisLine={false} />
                <Tooltip content={<ChartTooltip />} />
                <Area type="monotone" dataKey="forecast" name="Proyeksi" stroke="hsl(var(--secondary))" strokeDasharray="7 5" fill="url(#forecastFill)" strokeWidth={2.5} connectNulls />
                <Line type="monotone" dataKey="history" name="Historis" stroke="hsl(var(--primary))" strokeWidth={2.5} dot={false} />
              </AreaChart>
            </ResponsiveContainer>
            <div className="mt-4 flex flex-wrap items-center justify-between gap-2 text-xs text-muted-foreground">
              <div className="flex items-center gap-4">
                <span className="flex items-center gap-1.5"><i className="h-0.5 w-4 rounded bg-primary" /> Historis</span>
                <span className="flex items-center gap-1.5"><i className="h-0 w-4 border-t-2 border-dashed border-secondary" /> Proyeksi AI</span>
              </div>
              <span>Indeks ilustratif untuk demonstrasi produk.</span>
            </div>
          </FadeIn>

          <div className="grid gap-4">
            {metrics.map(({ label, value, badge, status }, index) => (
              <FadeIn key={label} delay={index * 0.05} className="liquid-glass flex flex-1 flex-col justify-center rounded-2xl p-5">
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
    { region: "Sulawesi Barat", commodity: "Tekanan tertinggi", trend: "+3.3%", status: "watch" as Status },
    { region: "Sulawesi Tengah", commodity: "Tekanan menengah", trend: "+2.3%", status: "watch" as Status },
    { region: "DKI Jakarta", commodity: "Pantauan harga", trend: "+2.1%", status: "stable" as Status },
    { region: "Kalimantan Utara", commodity: "Tren naik", trend: "+2.0%", status: "stable" as Status },
  ];

  return (
    <section id="heatmap" className="px-8 py-24 md:px-28 md:py-32">
      <div className="mx-auto max-w-7xl">
        <SectionHeading
          eyebrow="Peta Tekanan Harga"
          title={<>See inflation pressure <span className="font-serif-accent text-secondary">by region.</span></>}
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

          <FadeIn className="liquid-glass rounded-3xl p-6">
            <div className="flex items-center justify-between">
              <h3 className="text-xl font-semibold text-foreground">Top Provinsi Tertekan</h3>
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
          </FadeIn>
        </div>
      </div>
    </section>
  );
}

function EcosystemDiagram() {
  const reduceMotion = useReducedMotion();
  // Satellite node anchors in a 100×100 viewBox (matched to the node cards below).
  const nodes = [
    { id: "citizens", label: "Citizens", Icon: Users, x: 20, y: 20, pos: "left-[3%] top-[6%]" },
    { id: "tpid", label: "TPID", Icon: Landmark, x: 80, y: 20, pos: "right-[3%] top-[6%]" },
    { id: "msmes", label: "MSMEs", Icon: Sprout, x: 20, y: 80, pos: "left-[3%] bottom-[6%]" },
    { id: "finance", label: "Finance", Icon: Building2, x: 80, y: 80, pos: "right-[3%] bottom-[6%]" },
  ] as const;

  return (
    <div className="relative aspect-square w-full overflow-hidden rounded-3xl border border-white/10 bg-[radial-gradient(circle_at_center,hsl(var(--primary)/0.10),transparent_65%)] p-2">
      <div aria-hidden className="absolute inset-0 rice-texture opacity-[0.12]" />

      {/* Connector layer */}
      <svg
        className="absolute inset-0 h-full w-full"
        viewBox="0 0 100 100"
        preserveAspectRatio="none"
        aria-hidden
      >
        <defs>
          <linearGradient id="ecoLine" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0%" stopColor="hsl(var(--primary))" stopOpacity={0.15} />
            <stop offset="50%" stopColor="hsl(var(--secondary))" stopOpacity={0.55} />
            <stop offset="100%" stopColor="hsl(var(--primary))" stopOpacity={0.15} />
          </linearGradient>
        </defs>
        {nodes.map((n, i) => (
          <g key={n.id}>
            {/* Static base line */}
            <line
              x1={50}
              y1={50}
              x2={n.x}
              y2={n.y}
              stroke="hsl(var(--foreground) / 0.08)"
              strokeWidth={0.6}
            />
            {/* Animated flowing overlay */}
            <motion.line
              x1={50}
              y1={50}
              x2={n.x}
              y2={n.y}
              stroke="url(#ecoLine)"
              strokeWidth={0.9}
              strokeDasharray="6 10"
              initial={reduceMotion ? undefined : { strokeDashoffset: 0 }}
              animate={reduceMotion ? undefined : { strokeDashoffset: -32 }}
              transition={{
                duration: 2.4,
                ease: "linear",
                repeat: Infinity,
                delay: i * 0.3,
              }}
            />
          </g>
        ))}
      </svg>

      {/* Central hub */}
      <div className="absolute left-1/2 top-1/2 z-10 -translate-x-1/2 -translate-y-1/2">
        {!reduceMotion && (
          <>
            <motion.span
              className="absolute inset-0 -z-10 rounded-full border border-secondary/30"
              animate={{ scale: [1, 1.8], opacity: [0.5, 0] }}
              transition={{ duration: 2.8, repeat: Infinity, ease: "easeOut" }}
            />
            <motion.span
              className="absolute inset-0 -z-10 rounded-full border border-secondary/20"
              animate={{ scale: [1, 2.2], opacity: [0.35, 0] }}
              transition={{ duration: 2.8, repeat: Infinity, ease: "easeOut", delay: 1.4 }}
            />
          </>
        )}
        <div className="flex h-24 w-24 flex-col items-center justify-center gap-0.5 rounded-full border border-secondary/40 bg-secondary/15 text-secondary shadow-[0_0_40px_-8px_hsl(var(--secondary)/0.6)] backdrop-blur-sm">
          <Wheat className="h-9 w-9" />
          <span className="text-[9px] font-bold uppercase tracking-wider">Signal</span>
        </div>
      </div>

      {/* Satellite nodes */}
      {nodes.map(({ id, label, Icon, pos }) => (
        <div
          key={id}
          className={cn(
            "absolute z-10 flex items-center gap-2 rounded-2xl border border-white/10 bg-background/85 px-3 py-2.5 shadow-xl backdrop-blur-md",
            pos,
          )}
        >
          <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-secondary/15 text-secondary">
            <Icon className="h-4 w-4" />
          </span>
          <span className="text-sm font-semibold text-foreground">{label}</span>
        </div>
      ))}

      {/* Caption */}
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
    [Users, "Citizens", "Compare prices before visiting markets and receive price alerts."],
    [Landmark, "Local Governments", "Detect regional inflation pressure earlier and support TPID decision-making."],
    [Sprout, "Farmers & MSMEs", "Understand demand, price movement, and supply opportunities across regions."],
    [Building2, "Financial Institutions", "Use aggregated food price signals for parametric insurance, risk modeling, and agricultural credit insights."],
  ] as const;

  return (
    <section id="ecosystem" className="px-8 py-24 md:px-28 md:py-32">
      <div className="mx-auto max-w-7xl">
        <SectionHeading
          title="Built for the entire food resilience ecosystem."
          subtitle="Food price intelligence becomes more valuable when citizens, institutions, and supply actors share the same validated signal."
        />
        <div className="mt-14 grid gap-8 lg:grid-cols-[1fr_0.8fr] lg:items-center">
          <div className="grid gap-4 md:grid-cols-2">
            {cards.map(([Icon, title, copy], index) => (
              <FadeIn key={title} delay={index * 0.06} className="liquid-glass rounded-3xl p-8 transition hover:border-secondary/30">
                <Icon className="h-8 w-8 text-secondary" />
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
    ["Pemantau Pemula", "0-500 points", 18],
    ["Pengamat Aktif", "501-2.000 points", 42],
    ["Sentinel Harga", "2.001-10.000 points", 74],
    ["Pahlawan Pangan", "10.000+ points", 94],
  ] as const;
  const activities = ["+10 Lapor harga komoditas", "+5 Verifikasi data orang lain", "+25 Streak 7 hari", "+50 Challenge mingguan", "+30 Ajak kontributor baru"];

  return (
    <section className="px-8 py-24 md:px-28 md:py-32">
      <div className="mx-auto max-w-7xl">
        <SectionHeading
          title="Community-powered data that keeps improving."
          subtitle="Gamification helps maintain participation without relying only on cash incentives."
        />
        <div className="mt-14 grid gap-5 lg:grid-cols-[1.1fr_0.9fr]">
          <div className="grid gap-4 md:grid-cols-2">
            {levels.map(([title, range, progress], index) => (
              <FadeIn key={title} delay={index * 0.05} className="liquid-glass rounded-3xl p-6">
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
          <FadeIn className="liquid-glass rounded-3xl p-7">
            <h3 className="text-xl font-semibold text-foreground">Point Activities</h3>
            <div className="mt-6 space-y-3">
              {activities.map((activity) => (
                <div key={activity} className="flex items-center gap-3 rounded-2xl bg-white/[0.035] p-4 text-sm text-muted-foreground">
                  <BadgeCheck className="h-5 w-5 text-secondary" />
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

export function CTASection() {
  return (
    <section className="relative flex min-h-[70vh] items-center justify-center overflow-hidden px-8 py-24 text-center">
      <div aria-hidden className="absolute inset-0 bg-[radial-gradient(circle_at_center,hsl(var(--primary)/0.26),transparent_58%)]" />
      <div aria-hidden className="absolute inset-0 rice-texture opacity-20" />
      <FadeIn className="relative z-10 mx-auto max-w-5xl">
        <h2 className="text-balance text-4xl font-medium leading-tight tracking-[-1.4px] text-foreground md:text-7xl">
          Food resilience starts with <span className="font-serif-accent text-secondary">transparent data.</span>
        </h2>
        <p className="mx-auto mt-6 max-w-2xl text-lg leading-8 text-muted-foreground">
          Built for Indonesia. Powered by communities, validated data, and AI.
        </p>
        <div className="mt-9 flex flex-col items-center justify-center gap-3 sm:flex-row">
          <Button asChild className="h-12 rounded-full bg-secondary px-8 text-base font-semibold text-secondary-foreground hover:bg-secondary/90">
            <Link href="/login">Open Dashboard</Link>
          </Button>
          <Button asChild variant="outline" className="h-12 rounded-full border-white/15 bg-white/5 px-8 text-base text-foreground hover:bg-white/10 hover:text-foreground">
            <Link href="#ecosystem">Partner With Us</Link>
          </Button>
        </div>
        <p className="mt-8 text-sm text-muted-foreground">Designed for citizens, local governments, researchers, and financial institutions.</p>
      </FadeIn>
    </section>
  );
}

export function Footer() {
  const columns = [
    ["Platform", "Blog", "Dashboard", "Heatmap", "Forecasting"],
    ["Data", "Methodology", "Validation", "Coverage"],
    ["Ecosystem", "Government", "Fintech", "Insurance", "Research"],
    ["Company", "About", "Contact", "Partnership"],
  ];
  // Links that have a real destination; everything else is a placeholder anchor.
  const hrefs: Record<string, string> = {
    Blog: "/blog",
    Dashboard: "/welcome#dashboard",
    Heatmap: "/welcome#heatmap",
    Forecasting: "/welcome#forecasting",
  };

  return (
    <footer className="border-t border-white/10 px-8 py-12 md:px-28">
      <div className="mx-auto max-w-7xl">
        <div className="grid gap-10 md:grid-cols-[1.4fr_repeat(4,1fr)]">
          <div>
            <Link href="/welcome" className="flex items-center gap-3">
              <Image src="/logo.svg" alt="INFLASI ID" width={40} height={40} className="h-10 w-10 rounded-full" />
              <span className="text-xl font-bold tracking-tight text-foreground">inflasi.id</span>
            </Link>
            <p className="mt-3 max-w-xs text-sm leading-6 text-muted-foreground">Food Inflation Intelligence Platform</p>
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
        <p className="mt-12 border-t border-white/10 pt-6 text-xs text-muted-foreground">© 2026 inflasi.id - Food Inflation Intelligence Platform for Indonesia.</p>
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
      <CTASection />
      <Footer />
    </main>
  );
}
