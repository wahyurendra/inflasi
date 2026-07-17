"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useSubmitReport } from "@/hooks/use-reports";
import { useToast } from "@/hooks/use-toast";
import { MVP_COMMODITIES, REGIONS } from "@/lib/constants";
import { getRegenciesByProvince, getDistrictsByRegency } from "@/lib/wilayah";
import { Camera, Send, X, MapPin, LocateFixed, RefreshCw } from "lucide-react";

export default function LaporHargaPage() {
  const router = useRouter();
  const { toast } = useToast();
  const submitReport = useSubmitReport();

  const [commodityId, setCommodityId] = useState("");
  const [regionId, setRegionId] = useState("");
  const [harga, setHarga] = useState("");
  const [satuan, setSatuan] = useState("kg");
  const [namaPasar, setNamaPasar] = useState("");
  const [kabupatenKode, setKabupatenKode] = useState("");
  const [kota, setKota] = useState("");
  const [kecamatanKode, setKecamatanKode] = useState("");
  const [kecamatan, setKecamatan] = useState("");
  const [tanggal, setTanggal] = useState(
    new Date().toISOString().split("T")[0]
  );
  const [catatan, setCatatan] = useState("");
  const [photos, setPhotos] = useState<File[]>([]);
  const [photoUrls, setPhotoUrls] = useState<string[]>([]);
  const [gpsLocation, setGpsLocation] = useState<{ lat: number; lng: number; accuracy: number } | null>(null);
  const [gpsStatus, setGpsStatus] = useState<"idle" | "loading" | "error">("idle");

  // Auto-set satuan when commodity changes
  const handleCommodityChange = (value: string) => {
    setCommodityId(value);
    const commodity = MVP_COMMODITIES.find(
      (c) => c.kode === value
    );
    if (commodity) setSatuan(commodity.satuan);
  };

  // Kabupaten/kecamatan options depend on the parent selection — reset the
  // downstream choice whenever the parent changes so a stale name can't ship.
  const kabupatenOptions = regionId ? getRegenciesByProvince(regionId) : [];
  const kecamatanOptions = kabupatenKode ? getDistrictsByRegency(kabupatenKode) : [];

  const handleRegionChange = (value: string) => {
    setRegionId(value);
    setKabupatenKode("");
    setKota("");
    setKecamatanKode("");
    setKecamatan("");
  };

  const handleKabupatenChange = (value: string) => {
    const regency = kabupatenOptions.find((r) => r.code === value);
    setKabupatenKode(value);
    setKota(regency?.name ?? "");
    setKecamatanKode("");
    setKecamatan("");
  };

  const handleKecamatanChange = (value: string) => {
    const district = kecamatanOptions.find((d) => d.code === value);
    setKecamatanKode(value);
    setKecamatan(district?.name ?? "");
  };

  const handleGetLocation = () => {
    if (!navigator.geolocation) {
      toast({ title: "Geolocation tidak didukung browser ini", variant: "destructive" });
      return;
    }

    setGpsStatus("loading");
    navigator.geolocation.getCurrentPosition(
      (position) => {
        setGpsLocation({
          lat: position.coords.latitude,
          lng: position.coords.longitude,
          accuracy: position.coords.accuracy,
        });
        setGpsStatus("idle");
      },
      (error) => {
        setGpsStatus("error");
        const message =
          error.code === error.PERMISSION_DENIED
            ? "Izin lokasi ditolak. Aktifkan izin lokasi untuk browser ini."
            : error.code === error.TIMEOUT
            ? "Waktu deteksi lokasi habis. Coba lagi."
            : "Lokasi tidak dapat dideteksi. Coba lagi.";
        toast({ title: "Gagal mendapatkan lokasi", description: message, variant: "destructive" });
      },
      { enableHighAccuracy: true, timeout: 10000 }
    );
  };

  const handlePhotoUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (!files) return;

    const newPhotos = Array.from(files).slice(0, 3 - photos.length);

    for (const file of newPhotos) {
      if (file.size > 5 * 1024 * 1024) {
        toast({ title: "File terlalu besar", description: "Maksimal 5MB per foto", variant: "destructive" });
        continue;
      }

      const formData = new FormData();
      formData.append("file", file);

      try {
        const res = await fetch("/api/upload", { method: "POST", body: formData });
        if (res.ok) {
          const data = await res.json();
          setPhotos((prev) => [...prev, file]);
          setPhotoUrls((prev) => [...prev, data.url]);
        }
      } catch {
        toast({ title: "Upload gagal", variant: "destructive" });
      }
    }
  };

  const removePhoto = (index: number) => {
    setPhotos((prev) => prev.filter((_, i) => i !== index));
    setPhotoUrls((prev) => prev.filter((_, i) => i !== index));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    const commodity = MVP_COMMODITIES.find((c) => c.kode === commodityId);
    const region = REGIONS.find((r) => r.kode === regionId);

    if (!commodity || !region) {
      toast({ title: "Pilih komoditas dan wilayah", variant: "destructive" });
      return;
    }

    try {
      await submitReport.mutateAsync({
        commodityKode: commodity.kode,
        regionKode: region.kode,
        harga: parseFloat(harga),
        satuan,
        namaPasar,
        kota,
        kecamatan,
        latitude: gpsLocation?.lat,
        longitude: gpsLocation?.lng,
        tanggal,
        catatan: catatan || undefined,
        photoUrls,
      });

      toast({
        title: "Laporan terkirim",
        description: "Laporan Anda sedang ditinjau. Terima kasih!",
        variant: "success",
      });
      router.push("/laporan");
    } catch (error) {
      toast({
        title: "Gagal mengirim",
        description: error instanceof Error ? error.message : "Silakan coba lagi",
        variant: "destructive",
      });
    }
  };

  const provinces = REGIONS.filter((r) => r.level === "provinsi");

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <div>
        <h1 className="text-lg font-bold text-foreground">Lapor Harga</h1>
        <p className="text-sm text-muted-foreground">
          Laporkan harga komoditas pangan di pasar terdekat Anda
        </p>
      </div>

      <form onSubmit={handleSubmit} className="bg-card rounded-xl border p-6 space-y-5">
        {/* Commodity */}
        <div className="space-y-2">
          <Label>Komoditas *</Label>
          <Select value={commodityId} onValueChange={handleCommodityChange}>
            <SelectTrigger>
              <SelectValue placeholder="Pilih komoditas" />
            </SelectTrigger>
            <SelectContent>
              {MVP_COMMODITIES.map((c) => (
                <SelectItem key={c.kode} value={c.kode}>
                  {c.display}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        {/* Price & Unit */}
        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-2">
            <Label>Harga (Rp) *</Label>
            <div className="relative">
              <span className="absolute left-3 top-1/2 -translate-y-1/2 text-sm text-muted-foreground">
                Rp
              </span>
              <Input
                type="number"
                placeholder="0"
                value={harga}
                onChange={(e) => setHarga(e.target.value)}
                className="pl-10"
                required
                min="100"
              />
            </div>
          </div>
          <div className="space-y-2">
            <Label>Satuan</Label>
            <Input value={satuan} onChange={(e) => setSatuan(e.target.value)} />
          </div>
        </div>

        {/* Market */}
        <div className="space-y-2">
          <Label>Nama Pasar / Toko *</Label>
          <Input
            placeholder="Mis: Pasar Senen"
            value={namaPasar}
            onChange={(e) => setNamaPasar(e.target.value)}
            required
          />
        </div>

        {/* Location */}
        <div className="space-y-2">
          <Label>Provinsi *</Label>
          <Select value={regionId} onValueChange={handleRegionChange}>
            <SelectTrigger>
              <SelectValue placeholder="Pilih provinsi" />
            </SelectTrigger>
            <SelectContent>
              {provinces.map((r) => (
                <SelectItem key={r.kode} value={r.kode}>
                  {r.provinsi}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-2">
            <Label>Kota / Kabupaten</Label>
            <Select
              value={kabupatenKode}
              onValueChange={handleKabupatenChange}
              disabled={!regionId}
            >
              <SelectTrigger>
                <SelectValue placeholder={regionId ? "Pilih kota/kabupaten" : "Pilih provinsi dahulu"} />
              </SelectTrigger>
              <SelectContent>
                {kabupatenOptions.map((r) => (
                  <SelectItem key={r.code} value={r.code}>
                    {r.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-2">
            <Label>Kecamatan</Label>
            <Select
              value={kecamatanKode}
              onValueChange={handleKecamatanChange}
              disabled={!kabupatenKode}
            >
              <SelectTrigger>
                <SelectValue placeholder={kabupatenKode ? "Pilih kecamatan" : "Pilih kota/kabupaten dahulu"} />
              </SelectTrigger>
              <SelectContent>
                {kecamatanOptions.map((d) => (
                  <SelectItem key={d.code} value={d.code}>
                    {d.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </div>

        {/* GPS Location */}
        <div className="space-y-2">
          <Label>Lokasi GPS (Opsional)</Label>
          {gpsLocation ? (
            <div className="flex items-center justify-between gap-3 rounded-lg border bg-muted/40 p-3 text-sm">
              <div className="flex items-center gap-2 min-w-0">
                <MapPin className="h-4 w-4 text-primary shrink-0" />
                <div className="min-w-0">
                  <p className="font-mono text-xs">
                    {gpsLocation.lat.toFixed(6)}, {gpsLocation.lng.toFixed(6)}
                  </p>
                  <p className="text-xs text-muted-foreground">
                    Akurasi ±{Math.round(gpsLocation.accuracy)}m ·{" "}
                    <a
                      href={`https://www.google.com/maps?q=${gpsLocation.lat},${gpsLocation.lng}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="underline hover:text-foreground"
                    >
                      Buka di peta
                    </a>
                  </p>
                </div>
              </div>
              <Button
                type="button"
                variant="ghost"
                size="sm"
                onClick={handleGetLocation}
                disabled={gpsStatus === "loading"}
              >
                <RefreshCw className={`h-3.5 w-3.5 ${gpsStatus === "loading" ? "animate-spin" : ""}`} />
              </Button>
            </div>
          ) : (
            <Button
              type="button"
              variant="outline"
              onClick={handleGetLocation}
              disabled={gpsStatus === "loading"}
              className="w-full"
            >
              <LocateFixed className={`h-4 w-4 mr-2 ${gpsStatus === "loading" ? "animate-spin" : ""}`} />
              {gpsStatus === "loading" ? "Mendeteksi lokasi..." : "Ambil Lokasi Saat Ini"}
            </Button>
          )}
        </div>

        {/* Date */}
        <div className="space-y-2">
          <Label>Tanggal Laporan *</Label>
          <Input
            type="date"
            value={tanggal}
            onChange={(e) => setTanggal(e.target.value)}
            max={new Date().toISOString().split("T")[0]}
            required
          />
        </div>

        {/* Photos */}
        <div className="space-y-2">
          <Label>Foto Bukti (maks. 3)</Label>
          <div className="flex gap-3 flex-wrap">
            {photos.map((photo, i) => (
              <div key={i} className="relative w-20 h-20 rounded-lg border overflow-hidden bg-muted">
                <img
                  src={URL.createObjectURL(photo)}
                  alt="preview"
                  className="w-full h-full object-cover"
                />
                <button
                  type="button"
                  onClick={() => removePhoto(i)}
                  className="absolute top-0.5 right-0.5 bg-black/50 rounded-full p-0.5"
                >
                  <X className="h-3 w-3 text-white" />
                </button>
              </div>
            ))}
            {photos.length < 3 && (
              <label className="w-20 h-20 rounded-lg border-2 border-dashed flex items-center justify-center cursor-pointer hover:bg-muted transition-colors">
                <Camera className="h-5 w-5 text-muted-foreground" />
                <input
                  type="file"
                  accept="image/jpeg,image/png,image/webp"
                  onChange={handlePhotoUpload}
                  className="hidden"
                />
              </label>
            )}
          </div>
        </div>

        {/* Notes */}
        <div className="space-y-2">
          <Label>Catatan</Label>
          <Textarea
            placeholder="Catatan tambahan (opsional)"
            value={catatan}
            onChange={(e) => setCatatan(e.target.value)}
            rows={3}
          />
        </div>

        <Button type="submit" className="w-full" disabled={submitReport.isPending}>
          <Send className="h-4 w-4 mr-2" />
          {submitReport.isPending ? "Mengirim..." : "Kirim Laporan"}
        </Button>
      </form>
    </div>
  );
}
