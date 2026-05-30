"use client";

import { useState } from "react";
import { Send, CheckCircle2 } from "lucide-react";

const PARTNER_EMAIL = "partnership@inflasi.id";

const PARTNER_TYPES = [
  "Pemerintah / TPID",
  "Institusi Keuangan",
  "Riset & Akademik",
  "Media / NGO",
  "Pengembang / API",
  "Lainnya",
];

export function PartnerForm() {
  const [form, setForm] = useState({
    name: "",
    org: "",
    email: "",
    type: PARTNER_TYPES[0],
    message: "",
  });
  const [submitted, setSubmitted] = useState(false);

  const update = (k: keyof typeof form) => (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>,
  ) => setForm((f) => ({ ...f, [k]: e.target.value }));

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const subject = `Partnership Inquiry — ${form.org || form.name} (${form.type})`;
    const body = [
      `Nama: ${form.name}`,
      `Organisasi: ${form.org}`,
      `Email: ${form.email}`,
      `Jenis mitra: ${form.type}`,
      "",
      "Pesan:",
      form.message,
    ].join("\n");
    window.location.href = `mailto:${PARTNER_EMAIL}?subject=${encodeURIComponent(
      subject,
    )}&body=${encodeURIComponent(body)}`;
    setSubmitted(true);
  };

  const fieldClass =
    "w-full rounded-xl border border-white/10 bg-white/[0.03] px-4 py-3 text-sm text-foreground placeholder:text-muted-foreground/70 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-secondary/50 focus-visible:border-secondary/40 transition";

  if (submitted) {
    return (
      <div className="liquid-glass gold-glow rounded-3xl p-10 text-center">
        <CheckCircle2 className="mx-auto h-12 w-12 text-secondary" />
        <h3 className="mt-5 text-2xl font-semibold text-foreground">Terima kasih!</h3>
        <p className="mx-auto mt-3 max-w-md text-sm leading-6 text-muted-foreground">
          Email klien Anda akan terbuka dengan pesan yang sudah terisi. Jika tidak terbuka,
          kirim langsung ke{" "}
          <a href={`mailto:${PARTNER_EMAIL}`} className="text-secondary hover:underline">
            {PARTNER_EMAIL}
          </a>
          . Tim kami akan merespons dalam 2–3 hari kerja.
        </p>
        <button
          type="button"
          onClick={() => setSubmitted(false)}
          className="mt-6 text-sm font-medium text-secondary hover:underline"
        >
          Kirim pesan lain
        </button>
      </div>
    );
  }

  return (
    <form onSubmit={handleSubmit} className="liquid-glass rounded-3xl p-6 md:p-8">
      <div className="grid gap-4 sm:grid-cols-2">
        <div>
          <label htmlFor="name" className="mb-1.5 block text-xs font-medium text-muted-foreground">
            Nama lengkap *
          </label>
          <input
            id="name"
            required
            value={form.name}
            onChange={update("name")}
            placeholder="Nama Anda"
            className={fieldClass}
          />
        </div>
        <div>
          <label htmlFor="org" className="mb-1.5 block text-xs font-medium text-muted-foreground">
            Organisasi *
          </label>
          <input
            id="org"
            required
            value={form.org}
            onChange={update("org")}
            placeholder="Nama instansi / perusahaan"
            className={fieldClass}
          />
        </div>
      </div>

      <div className="mt-4 grid gap-4 sm:grid-cols-2">
        <div>
          <label htmlFor="email" className="mb-1.5 block text-xs font-medium text-muted-foreground">
            Email *
          </label>
          <input
            id="email"
            type="email"
            required
            value={form.email}
            onChange={update("email")}
            placeholder="nama@organisasi.go.id"
            className={fieldClass}
          />
        </div>
        <div>
          <label htmlFor="type" className="mb-1.5 block text-xs font-medium text-muted-foreground">
            Jenis kemitraan
          </label>
          <select id="type" value={form.type} onChange={update("type")} className={fieldClass}>
            {PARTNER_TYPES.map((t) => (
              <option key={t} value={t} className="bg-background text-foreground">
                {t}
              </option>
            ))}
          </select>
        </div>
      </div>

      <div className="mt-4">
        <label htmlFor="message" className="mb-1.5 block text-xs font-medium text-muted-foreground">
          Ceritakan kebutuhan Anda *
        </label>
        <textarea
          id="message"
          required
          rows={5}
          value={form.message}
          onChange={update("message")}
          placeholder="Misal: kami ingin mengakses data harga pangan regional untuk model risiko kredit pertanian…"
          className={`${fieldClass} resize-none`}
        />
      </div>

      <button
        type="submit"
        className="mt-6 inline-flex w-full items-center justify-center gap-2 rounded-full bg-secondary px-8 py-3.5 text-sm font-semibold text-secondary-foreground transition hover:bg-secondary/90 sm:w-auto"
      >
        <Send className="h-4 w-4" />
        Kirim Permintaan Kemitraan
      </button>
      <p className="mt-4 text-xs text-muted-foreground">
        Atau email langsung ke{" "}
        <a href={`mailto:${PARTNER_EMAIL}`} className="text-secondary hover:underline">
          {PARTNER_EMAIL}
        </a>
      </p>
    </form>
  );
}
