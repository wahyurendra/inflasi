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
import { Camera, Send, X } from "lucide-react";

export default function LaporHargaPage() {
  const router = useRouter();
  const { toast } = useToast();
  const submitReport = useSubmitReport();

  const [commodityId, setCommodityId] = useState("");
  const [regionId, setRegionId] = useState("");
  const [harga, setHarga] = useState("");
  const [satuan, setSatuan] = useState("kg");
  const [namaPasar, setNamaPasar] = useState("");
  const [kota, setKota] = useState("");
  const [kecamatan, setKecamatan] = useState("");
  const [tanggal, setTanggal] = useState(
    new Date().toISOString().split("T")[0]
  );
  const [catatan, setCatatan] = useState("");
  const [photos, setPhotos] = useState<File[]>([]);
  const [photoUrls, setPhotoUrls] = useState<string[]>([]);

  // Auto-set satuan when commodity changes
  const handleCommodityChange = (value: string) => {
    setCommodityId(value);
    const commodity = MVP_COMMODITIES.find(
      (c) => c.kode === value
    );
    if (commodity) setSatuan(commodity.satuan);
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

    const commodityIndex = MVP_COMMODITIES.findIndex((c) => c.kode === commodityId);
    const regionIndex = REGIONS.findIndex((r) => r.kode === regionId);

    if (commodityIndex === -1 || regionIndex === -1) {
      toast({ title: "Pilih komoditas dan wilayah", variant: "destructive" });
      return;
    }

    try {
      await submitReport.mutateAsync({
        commodityId: commodityIndex + 1,
        regionId: regionIndex + 1,
        harga: parseFloat(harga),
        satuan,
        namaPasar,
        kota,
        kecamatan,
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
          <Select value={regionId} onValueChange={setRegionId}>
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
            <Input
              placeholder="Opsional"
              value={kota}
              onChange={(e) => setKota(e.target.value)}
            />
          </div>
          <div className="space-y-2">
            <Label>Kecamatan</Label>
            <Input
              placeholder="Opsional"
              value={kecamatan}
              onChange={(e) => setKecamatan(e.target.value)}
            />
          </div>
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
