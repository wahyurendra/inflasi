import type { Metadata } from "next";
import Link from "next/link";
import { apiClient } from "@/lib/api-client";
import { Navbar, Footer } from "@/components/landing/premium-landing";
import { ArrowRight, CalendarDays, Newspaper } from "lucide-react";

export const dynamic = "force-dynamic";

const siteUrl = process.env.NEXT_PUBLIC_APP_URL || "https://inflasi.id";

const description =
  "Analisis harian inflasi pangan Indonesia: ringkasan harga komoditas, wilayah tertekan, dan faktor pendorong — otomatis dari data terbaru inflasi.id.";

export const metadata: Metadata = {
  title: "Blog — Analisis Harga & Inflasi Pangan",
  description,
  alternates: { canonical: "/blog" },
  openGraph: {
    type: "website",
    url: `${siteUrl}/blog`,
    title: "Blog Inflasi.id — Analisis Harga & Inflasi Pangan",
    description,
  },
};

interface BlogSummary {
  slug: string;
  title: string;
  excerpt: string;
  tanggal: string;
  published_at: string | null;
  tags: string[] | null;
}

function formatDate(value: string | null): string {
  if (!value) return "";
  try {
    return new Date(value).toLocaleDateString("id-ID", {
      day: "numeric",
      month: "long",
      year: "numeric",
    });
  } catch {
    return value;
  }
}

async function getPosts(): Promise<BlogSummary[]> {
  try {
    const res = await apiClient.get<{ data: BlogSummary[] }>("/blog", { limit: "30" });
    return res.data ?? [];
  } catch {
    return [];
  }
}

export default async function BlogIndexPage() {
  const posts = await getPosts();

  return (
    <main className="landing-theme min-h-screen bg-background text-foreground">
      <Navbar />
      <section className="mx-auto max-w-5xl px-6 pb-24 pt-32 md:pt-36">
        <header className="mb-12 text-center">
          <p className="mb-4 inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-4 py-1.5 text-xs font-semibold uppercase tracking-[0.18em] text-secondary">
            <Newspaper className="h-3.5 w-3.5" />
            Blog
          </p>
          <h1 className="text-balance text-4xl font-medium leading-tight tracking-[-1.4px] md:text-6xl">
            Analisis Harga &amp; <span className="font-serif-accent text-secondary">Inflasi Pangan</span>
          </h1>
          <p className="mx-auto mt-5 max-w-2xl text-base leading-7 text-muted-foreground">
            {description}
          </p>
        </header>

        {posts.length === 0 ? (
          <div className="liquid-glass rounded-3xl p-12 text-center">
            <Newspaper className="mx-auto mb-3 h-8 w-8 text-muted-foreground/40" />
            <p className="text-sm text-muted-foreground">
              Belum ada artikel. Artikel pertama akan terbit otomatis setelah batch analitik harian berjalan.
            </p>
          </div>
        ) : (
          <div className="grid gap-5 md:grid-cols-2">
            {posts.map((post) => (
              <Link
                key={post.slug}
                href={`/blog/${post.slug}`}
                className="liquid-glass group flex flex-col rounded-3xl p-6 transition hover:border-secondary/30"
              >
                <div className="mb-3 flex items-center gap-2 text-[11px] text-muted-foreground">
                  <CalendarDays className="h-3.5 w-3.5" />
                  {formatDate(post.published_at || post.tanggal)}
                </div>
                <h2 className="text-xl font-semibold leading-snug tracking-tight text-foreground">
                  {post.title}
                </h2>
                <p className="mt-2 line-clamp-3 flex-1 text-sm leading-6 text-muted-foreground">
                  {post.excerpt}
                </p>
                {post.tags && post.tags.length > 0 && (
                  <div className="mt-4 flex flex-wrap gap-1.5">
                    {post.tags.slice(0, 4).map((tag) => (
                      <span
                        key={tag}
                        className="rounded-full bg-white/[0.04] px-2 py-0.5 text-[10px] text-muted-foreground"
                      >
                        {tag}
                      </span>
                    ))}
                  </div>
                )}
                <span className="mt-5 inline-flex items-center gap-1.5 text-sm font-semibold text-secondary">
                  Baca selengkapnya
                  <ArrowRight className="h-3.5 w-3.5 transition group-hover:translate-x-0.5" />
                </span>
              </Link>
            ))}
          </div>
        )}
      </section>
      <Footer />
    </main>
  );
}
