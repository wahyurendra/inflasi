import Link from "next/link";
import {
  BarChart3,
  MapPin,
  Users,
  Bell,
  Brain,
  TrendingUp,
  ShieldCheck,
  Globe,
  ArrowRight,
} from "lucide-react";

const features = [
  {
    icon: BarChart3,
    title: "Dashboard Real-time",
    description: "Pantau harga 10 komoditas strategis secara real-time dari 34 provinsi.",
  },
  {
    icon: MapPin,
    title: "Peta Harga Interaktif",
    description: "Visualisasi peta choropleth inflasi per provinsi dengan data terkini.",
  },
  {
    icon: Users,
    title: "Crowdsourced Reporting",
    description: "Laporan harga dari masyarakat dengan validasi otomatis dan gamifikasi.",
  },
  {
    icon: Bell,
    title: "Early Warning System",
    description: "Deteksi dini lonjakan harga dengan threshold monitoring dan notifikasi.",
  },
  {
    icon: Brain,
    title: "AI-Powered Analysis",
    description: "Analisis tren, prediksi harga, dan rekomendasi kebijakan berbasis AI.",
  },
  {
    icon: TrendingUp,
    title: "Price Intelligence",
    description: "Perbandingan harga antar wilayah, volatilitas, dan price gap analysis.",
  },
];

const stats = [
  { value: "34", label: "Provinsi" },
  { value: "10", label: "Komoditas" },
  { value: "24/7", label: "Monitoring" },
  { value: "AI", label: "Powered" },
];

export default function LandingPage() {
  return (
    <div className="min-h-screen">
      {/* Navbar */}
      <nav className="border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 sticky top-0 z-50">
        <div className="max-w-6xl mx-auto px-4 h-14 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="h-8 w-8 rounded-lg bg-primary flex items-center justify-center">
              <TrendingUp className="h-4 w-4 text-primary-foreground" />
            </div>
            <span className="font-bold text-lg">Inflasi.id</span>
          </div>
          <div className="flex items-center gap-3">
            <Link
              href="/login"
              className="text-sm text-muted-foreground hover:text-foreground transition-colors"
            >
              Masuk
            </Link>
            <Link
              href="/register"
              className="text-sm bg-primary text-primary-foreground px-4 py-2 rounded-lg hover:bg-primary/90 transition-colors"
            >
              Daftar
            </Link>
          </div>
        </div>
      </nav>

      {/* Hero */}
      <section className="py-20 px-4">
        <div className="max-w-4xl mx-auto text-center">
          <div className="inline-flex items-center gap-2 bg-primary/10 text-primary px-3 py-1 rounded-full text-sm font-medium mb-6">
            <ShieldCheck className="h-4 w-4" />
            Platform Pemantauan Inflasi Pangan
          </div>
          <h1 className="text-4xl sm:text-5xl font-bold text-foreground mb-4 leading-tight">
            Pantau Harga Pangan{" "}
            <span className="text-primary">Seluruh Indonesia</span>
          </h1>
          <p className="text-lg text-muted-foreground max-w-2xl mx-auto mb-8">
            Sistem pemantauan inflasi pangan berbasis AI dengan data crowdsourced dari seluruh
            Indonesia. Deteksi dini lonjakan harga, analisis tren, dan rekomendasi kebijakan.
          </p>
          <div className="flex items-center justify-center gap-4">
            <Link
              href="/register"
              className="bg-primary text-primary-foreground px-6 py-3 rounded-lg font-medium hover:bg-primary/90 transition-colors flex items-center gap-2"
            >
              Mulai Sekarang
              <ArrowRight className="h-4 w-4" />
            </Link>
            <Link
              href="/login"
              className="border border-border px-6 py-3 rounded-lg font-medium hover:bg-muted transition-colors"
            >
              Masuk Dashboard
            </Link>
          </div>
        </div>
      </section>

      {/* Stats Bar */}
      <section className="border-y bg-muted/30 py-8 px-4">
        <div className="max-w-4xl mx-auto grid grid-cols-2 sm:grid-cols-4 gap-6">
          {stats.map((stat) => (
            <div key={stat.label} className="text-center">
              <p className="text-3xl font-bold text-primary">{stat.value}</p>
              <p className="text-sm text-muted-foreground">{stat.label}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Features */}
      <section className="py-20 px-4">
        <div className="max-w-5xl mx-auto">
          <div className="text-center mb-12">
            <h2 className="text-2xl font-bold mb-2">Fitur Utama</h2>
            <p className="text-muted-foreground">
              Platform komprehensif untuk pemantauan dan analisis harga pangan
            </p>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
            {features.map((feature) => (
              <div
                key={feature.title}
                className="bg-card rounded-xl border p-6 hover:shadow-md transition-shadow"
              >
                <div className="h-10 w-10 rounded-lg bg-primary/10 flex items-center justify-center mb-4">
                  <feature.icon className="h-5 w-5 text-primary" />
                </div>
                <h3 className="font-semibold mb-2">{feature.title}</h3>
                <p className="text-sm text-muted-foreground">{feature.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-16 px-4 bg-primary/5 border-t">
        <div className="max-w-3xl mx-auto text-center">
          <Globe className="h-10 w-10 text-primary mx-auto mb-4" />
          <h2 className="text-2xl font-bold mb-2">
            Bergabung dengan Inflasi.id
          </h2>
          <p className="text-muted-foreground mb-6">
            Bantu pantau harga pangan di wilayah Anda. Kontribusi Anda membantu pemerintah
            mengambil kebijakan yang tepat untuk stabilitas harga.
          </p>
          <Link
            href="/register"
            className="inline-flex items-center gap-2 bg-primary text-primary-foreground px-6 py-3 rounded-lg font-medium hover:bg-primary/90 transition-colors"
          >
            Daftar Sebagai Reporter
            <ArrowRight className="h-4 w-4" />
          </Link>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t py-8 px-4">
        <div className="max-w-6xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <div className="h-6 w-6 rounded bg-primary flex items-center justify-center">
              <TrendingUp className="h-3 w-3 text-primary-foreground" />
            </div>
            <span className="text-sm font-semibold">Inflasi.id</span>
          </div>
          <p className="text-xs text-muted-foreground">
            &copy; {new Date().getFullYear()} Inflasi.id — Sistem Pemantauan Inflasi Pangan Berbasis AI
          </p>
        </div>
      </footer>
    </div>
  );
}
