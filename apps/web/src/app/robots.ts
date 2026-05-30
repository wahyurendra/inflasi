import type { MetadataRoute } from "next";

const siteUrl = process.env.NEXT_PUBLIC_APP_URL || "https://inflasi.id";

export default function robots(): MetadataRoute.Robots {
  return {
    rules: [
      {
        userAgent: "*",
        allow: "/",
        // Keep authenticated app surfaces and API proxy out of the index.
        disallow: [
          "/api/",
          "/beranda",
          "/admin",
          "/validasi",
          "/laporan",
          "/lapor",
          "/notifications",
          "/profil",
          "/pengaturan",
          "/login",
          "/register",
        ],
      },
    ],
    sitemap: `${siteUrl}/sitemap.xml`,
    host: siteUrl,
  };
}
