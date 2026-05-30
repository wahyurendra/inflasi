import type { MetadataRoute } from "next";

export default function manifest(): MetadataRoute.Manifest {
  return {
    name: "Inflasi.id — Pemantauan Inflasi Pangan Indonesia",
    short_name: "Inflasi.id",
    description:
      "Intelijen inflasi pangan berbasis AI: harga harian, heatmap 38 provinsi, forecast, dan deteksi anomali.",
    start_url: "/",
    display: "standalone",
    background_color: "#0e1512",
    theme_color: "#0e1512",
    lang: "id-ID",
    categories: ["business", "finance", "productivity"],
    icons: [
      { src: "/icon.svg", sizes: "any", type: "image/svg+xml", purpose: "any" },
      { src: "/logo.svg", sizes: "any", type: "image/svg+xml", purpose: "maskable" },
    ],
  };
}
