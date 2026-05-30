export default function LandingLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="landing-theme min-h-screen bg-background text-foreground">
      {children}
    </div>
  );
}
