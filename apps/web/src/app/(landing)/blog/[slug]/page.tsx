import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { apiClient } from "@/lib/api-client";
import { Navbar, Footer } from "@/components/landing/premium-landing";
import { BlogProse } from "@/components/blog/blog-prose";
import { ArrowLeft, CalendarDays } from "lucide-react";

export const dynamic = "force-dynamic";

const siteUrl = process.env.NEXT_PUBLIC_APP_URL || "https://inflasi.id";

interface BlogPost {
  slug: string;
  title: string;
  excerpt: string;
  body_md: string;
  tanggal: string;
  published_at: string | null;
  tags: string[] | null;
}

async function getPost(slug: string): Promise<BlogPost | null> {
  try {
    return await apiClient.get<BlogPost>(`/blog/${slug}`);
  } catch {
    return null;
  }
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

export async function generateMetadata({
  params,
}: {
  params: { slug: string };
}): Promise<Metadata> {
  const post = await getPost(params.slug);
  if (!post) {
    return { title: "Artikel tidak ditemukan", robots: { index: false } };
  }
  const url = `${siteUrl}/blog/${post.slug}`;
  return {
    title: post.title,
    description: post.excerpt,
    alternates: { canonical: `/blog/${post.slug}` },
    openGraph: {
      type: "article",
      url,
      title: post.title,
      description: post.excerpt,
      publishedTime: post.published_at || undefined,
      tags: post.tags || undefined,
    },
    twitter: {
      card: "summary_large_image",
      title: post.title,
      description: post.excerpt,
    },
  };
}

export default async function BlogPostPage({
  params,
}: {
  params: { slug: string };
}) {
  const post = await getPost(params.slug);
  if (!post) notFound();

  const published = post.published_at || post.tanggal;
  const jsonLd = {
    "@context": "https://schema.org",
    "@type": "BlogPosting",
    headline: post.title,
    description: post.excerpt,
    datePublished: published,
    dateModified: published,
    inLanguage: "id-ID",
    keywords: (post.tags || []).join(", "),
    mainEntityOfPage: { "@type": "WebPage", "@id": `${siteUrl}/blog/${post.slug}` },
    author: { "@type": "Organization", name: "Inflasi.id", url: siteUrl },
    publisher: {
      "@type": "Organization",
      name: "Inflasi.id",
      logo: { "@type": "ImageObject", url: `${siteUrl}/logo.svg` },
    },
  };

  return (
    <main className="landing-theme min-h-screen bg-background text-foreground">
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
      />
      <Navbar />
      <article className="mx-auto max-w-3xl px-6 pb-24 pt-32 md:pt-36">
        <Link
          href="/blog"
          className="inline-flex items-center gap-1.5 text-sm text-muted-foreground transition hover:text-foreground"
        >
          <ArrowLeft className="h-3.5 w-3.5" />
          Semua artikel
        </Link>

        <header className="mb-8 mt-6">
          <div className="mb-4 flex items-center gap-2 text-xs text-muted-foreground">
            <CalendarDays className="h-3.5 w-3.5" />
            {formatDate(published)}
          </div>
          <h1 className="text-balance text-3xl font-medium leading-tight tracking-[-1px] md:text-5xl">
            {post.title}
          </h1>
          {post.excerpt && (
            <p className="mt-4 text-lg leading-7 text-hero-subtitle opacity-90">
              {post.excerpt}
            </p>
          )}
          {post.tags && post.tags.length > 0 && (
            <div className="mt-5 flex flex-wrap gap-1.5">
              {post.tags.map((tag) => (
                <span
                  key={tag}
                  className="rounded-full border border-white/10 bg-white/[0.04] px-2.5 py-1 text-[11px] text-muted-foreground"
                >
                  {tag}
                </span>
              ))}
            </div>
          )}
        </header>

        <hr className="mb-8 border-white/10" />

        <BlogProse markdown={post.body_md} />

        <div className="mt-12 rounded-2xl border border-white/10 bg-white/[0.025] p-6 text-center">
          <p className="text-sm text-muted-foreground">
            Pantau pergerakan harga pangan secara real-time di dashboard Inflasi.id.
          </p>
          <Link
            href="/login"
            className="mt-3 inline-flex items-center gap-1.5 rounded-full bg-secondary px-5 py-2.5 text-sm font-semibold text-secondary-foreground transition hover:bg-secondary/90"
          >
            Buka Dashboard
          </Link>
        </div>
      </article>
      <Footer />
    </main>
  );
}
