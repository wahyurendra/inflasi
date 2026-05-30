import Image from "next/image";
import Link from "next/link";

const BRAND_NAME = "{BRAND_NAME}";
const TAGLINE = "{FOOTER_TAGLINE}";

const COLUMNS = [
  {
    title: "Produk",
    links: [
      { label: "Fitur", href: "#features" },
      { label: "Harga", href: "#pricing" },
      { label: "FAQ", href: "#faq" },
      { label: "Dashboard", href: "/login" },
    ],
  },
  {
    title: "Perusahaan",
    links: [
      { label: "Tentang", href: "#about" },
      { label: "Blog", href: "{LINK_BLOG}" },
      { label: "Karir", href: "{LINK_CAREERS}" },
      { label: "Kontak", href: "{LINK_CONTACT}" },
    ],
  },
  {
    title: "Legal",
    links: [
      { label: "Privacy", href: "{LINK_PRIVACY}" },
      { label: "Terms", href: "{LINK_TERMS}" },
    ],
  },
];

export function LandingFooter() {
  return (
    <footer className="border-t bg-muted/30 px-4 pt-14 pb-8">
      <div className="max-w-6xl mx-auto">
        <div className="grid grid-cols-2 md:grid-cols-5 gap-8 mb-10">
          <div className="col-span-2">
            <Link href="/welcome" className="flex items-center gap-2.5 mb-3">
              <Image src="/logo.svg" alt={BRAND_NAME} width={36} height={36} />
              <span className="font-bold text-lg tracking-tight">{BRAND_NAME}</span>
            </Link>
            <p className="text-sm text-muted-foreground max-w-xs leading-relaxed">{TAGLINE}</p>
          </div>
          {COLUMNS.map((col) => (
            <div key={col.title}>
              <p className="font-semibold text-sm mb-3">{col.title}</p>
              <ul className="space-y-2">
                {col.links.map((l) => (
                  <li key={l.label}>
                    <Link
                      href={l.href}
                      className="text-sm text-muted-foreground hover:text-foreground transition-colors"
                    >
                      {l.label}
                    </Link>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
        <div className="border-t pt-6 flex flex-col sm:flex-row items-center justify-between gap-3">
          <p className="text-xs text-muted-foreground">
            &copy; {new Date().getFullYear()} {BRAND_NAME}. All rights reserved.
          </p>
          <p className="text-xs text-muted-foreground">
            Made in Indonesia · <span className="text-gold">●</span> Powered by AI
          </p>
        </div>
      </div>
    </footer>
  );
}
