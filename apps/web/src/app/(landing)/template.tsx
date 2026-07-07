import { PageTransition } from "@/components/page-transition";

// Template ter-mount ulang di tiap navigasi, jadi animasi enter halaman
// dimainkan setiap kali masuk/berpindah halaman dalam grup landing.
export default function LandingTemplate({
  children,
}: {
  children: React.ReactNode;
}) {
  return <PageTransition>{children}</PageTransition>;
}
