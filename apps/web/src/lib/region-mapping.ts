import { REGIONS, MVP_COMMODITIES } from "@/lib/constants";

// ============================================================
// Region code mapping
// ============================================================
// Backend stores region codes as slugs (e.g. "jawa_barat", "nasional").
// The FE uses canonical BPS numeric codes (e.g. "32", "00") because that
// matches the SVG choropleth paths and the REGIONS constant. This module
// bridges the two so backend responses can be normalised at the BFF, and
// outbound query params can be translated to the backend's expected slugs.

const REGION_NAME_TO_BPS = new Map<string, string>(
  REGIONS.map((r) => [r.provinsi.toLowerCase(), r.kode]),
);

const REGION_SLUG_TO_BPS = new Map<string, string>(
  REGIONS.map((r) => [
    r.provinsi.toLowerCase().replace(/\s+/g, "_"),
    r.kode,
  ]),
);

const REGION_BPS_TO_SLUG = new Map<string, string>(
  REGIONS.map((r) => [
    r.kode,
    r.provinsi.toLowerCase().replace(/\s+/g, "_"),
  ]),
);

/**
 * Backend slug → canonical BPS numeric code. Matches by `namaProvinsi` first
 * (most robust against slug-format drift) then falls back to slug lookup.
 * Unknown codes pass through unchanged.
 */
export function toBpsCode(rawCode: string, namaProvinsi?: string): string {
  if (namaProvinsi) {
    const byName = REGION_NAME_TO_BPS.get(namaProvinsi.toLowerCase());
    if (byName) return byName;
  }
  const bySlug = REGION_SLUG_TO_BPS.get(rawCode?.toLowerCase?.() ?? "");
  if (bySlug) return bySlug;
  return rawCode;
}

/**
 * Canonical BPS numeric code → backend slug. Used to translate outbound
 * query parameters. Returns the original value when no mapping exists so
 * the backend can still parse codes we don't know about.
 */
export function toBackendRegion(bpsCode: string): string {
  return REGION_BPS_TO_SLUG.get(bpsCode) ?? bpsCode;
}

// ============================================================
// Commodity code mapping
// ============================================================
// Backend stores commodity codes lowercase (e.g. "cabai_merah"). The FE
// constants in MVP_COMMODITIES use uppercase (e.g. "CABAI_MERAH"). Convert
// in both directions at the BFF layer.

const COMMODITY_KODES = new Set(MVP_COMMODITIES.map((c) => c.kode));

/**
 * FE commodity kode (uppercase) → backend kode (lowercase).
 */
export function toBackendCommodity(feKode: string): string {
  return feKode.toLowerCase();
}

/**
 * Backend commodity kode (lowercase) → FE kode (uppercase). When the
 * uppercased value isn't a known MVP commodity we still return uppercase
 * so the FE can use it as a stable key.
 */
export function toFrontendCommodity(dbKode: string): string {
  const upper = dbKode.toUpperCase();
  // Touch COMMODITY_KODES so the lookup is meaningful — keeps the set as
  // documentation of which codes are first-class without changing behaviour.
  void COMMODITY_KODES;
  return upper;
}
