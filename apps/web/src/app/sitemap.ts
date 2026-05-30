import type { MetadataRoute } from "next";
import { apiClient } from "@/lib/api-client";

const siteUrl = process.env.NEXT_PUBLIC_APP_URL || "https://inflasi.id";

interface BlogSummary {
  slug: string;
  published_at: string | null;
  tanggal: string;
}

async function blogEntries(): Promise<MetadataRoute.Sitemap> {
  try {
    const res = await apiClient.get<{ data: BlogSummary[] }>("/blog", { limit: "1000" });
    return (res.data ?? []).map((p) => ({
      url: `${siteUrl}/blog/${p.slug}`,
      lastModified: new Date(p.published_at || p.tanggal),
      changeFrequency: "monthly" as const,
      priority: 0.7,
    }));
  } catch {
    // Backend unavailable at build/request time — degrade to static routes.
    return [];
  }
}

export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  const now = new Date();
  const staticRoutes: MetadataRoute.Sitemap = [
    {
      url: siteUrl,
      lastModified: now,
      changeFrequency: "daily",
      priority: 1,
    },
    {
      url: `${siteUrl}/welcome`,
      lastModified: now,
      changeFrequency: "weekly",
      priority: 0.9,
    },
    {
      url: `${siteUrl}/blog`,
      lastModified: now,
      changeFrequency: "daily",
      priority: 0.8,
    },
  ];

  return [...staticRoutes, ...(await blogEntries())];
}
