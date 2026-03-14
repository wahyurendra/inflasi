export default function AuthLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-green-50 to-white dark:from-gray-950 dark:to-gray-900 p-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-primary">Inflasi.id</h1>
          <p className="text-sm text-muted-foreground mt-1">
            Sistem Pemantauan Harga Pangan Indonesia
          </p>
        </div>
        {children}
      </div>
    </div>
  );
}
