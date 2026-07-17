// Kabupaten/Kota (regency) and Kecamatan (district) reference data, sourced
// from BPS/Kemendagri administrative-area data (idn-area-data, ODbL license —
// see src/lib/data/wilayah/NOTICE.md). Bundled statically since the app has
// no backend dimension for regions below province level.

import regenciesData from "@/lib/data/wilayah/regencies.json";
import districtsData from "@/lib/data/wilayah/districts.json";

export interface Regency {
  code: string;
  provinceCode: string;
  name: string;
}

export interface District {
  code: string;
  regencyCode: string;
  name: string;
}

const regencies = regenciesData as Regency[];
const districts = districtsData as District[];

/** Kabupaten/Kota for a given province BPS code (e.g. "31" -> DKI Jakarta's 6 kota/kabupaten). */
export function getRegenciesByProvince(provinceCode: string): Regency[] {
  return regencies.filter((r) => r.provinceCode === provinceCode);
}

/** Kecamatan for a given kabupaten/kota code (e.g. "31.71" -> Jakarta Selatan's kecamatan). */
export function getDistrictsByRegency(regencyCode: string): District[] {
  return districts.filter((d) => d.regencyCode === regencyCode);
}
