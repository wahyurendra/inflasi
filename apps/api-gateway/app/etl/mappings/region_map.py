"""Mapping nama wilayah dari berbagai sumber ke kode `dim_region`.

History note: an earlier iteration of this map emitted 2-digit BPS province
codes (e.g. "11" for Aceh). The dimension table has since been resnapped to
human-readable slug codes (e.g. "aceh", "dki_jakarta") that match
`feature_store_daily` rows seeded from the training notebook. This map now
returns those slugs directly; downstream pipelines need no further translation.

Each entry below is a variant string the source emits → slug stored in
`dim_region.kode_wilayah`.
"""

# Slug values must match dim_region.kode_wilayah exactly.
REGION_NAME_TO_CODE: dict[str, str] = {
    # Nasional
    "nasional": "nasional",
    "indonesia": "nasional",
    "national": "nasional",
    # Aceh
    "aceh": "aceh",
    "prov. aceh": "aceh",
    "nanggroe aceh darussalam": "aceh",
    "nad": "aceh",
    # Sumatera Utara
    "sumatera utara": "sumatera_utara",
    "prov. sumatera utara": "sumatera_utara",
    "sumut": "sumatera_utara",
    "sumatera utara (medan)": "sumatera_utara",
    # Sumatera Barat
    "sumatera barat": "sumatera_barat",
    "prov. sumatera barat": "sumatera_barat",
    "sumbar": "sumatera_barat",
    # Riau
    "riau": "riau",
    "prov. riau": "riau",
    # Jambi
    "jambi": "jambi",
    "prov. jambi": "jambi",
    # Sumatera Selatan
    "sumatera selatan": "sumatera_selatan",
    "prov. sumatera selatan": "sumatera_selatan",
    "sumsel": "sumatera_selatan",
    # Bengkulu
    "bengkulu": "bengkulu",
    "prov. bengkulu": "bengkulu",
    # Lampung
    "lampung": "lampung",
    "prov. lampung": "lampung",
    # Kep. Bangka Belitung
    "kepulauan bangka belitung": "kepulauan_bangka_belitung",
    "bangka belitung": "kepulauan_bangka_belitung",
    "babel": "kepulauan_bangka_belitung",
    "kep. bangka belitung": "kepulauan_bangka_belitung",
    # Kep. Riau
    "kepulauan riau": "kepulauan_riau",
    "kep. riau": "kepulauan_riau",
    "kepri": "kepulauan_riau",
    # DKI Jakarta
    "dki jakarta": "dki_jakarta",
    "prov. dki jakarta": "dki_jakarta",
    "jakarta": "dki_jakarta",
    # Jawa Barat
    "jawa barat": "jawa_barat",
    "prov. jawa barat": "jawa_barat",
    "jabar": "jawa_barat",
    # Jawa Tengah
    "jawa tengah": "jawa_tengah",
    "prov. jawa tengah": "jawa_tengah",
    "jateng": "jawa_tengah",
    # DI Yogyakarta
    "di yogyakarta": "di_yogyakarta",
    "d.i. yogyakarta": "di_yogyakarta",
    "yogyakarta": "di_yogyakarta",
    "diy": "di_yogyakarta",
    "jogja": "di_yogyakarta",
    # Jawa Timur
    "jawa timur": "jawa_timur",
    "prov. jawa timur": "jawa_timur",
    "jatim": "jawa_timur",
    # Banten
    "banten": "banten",
    "prov. banten": "banten",
    # Bali
    "bali": "bali",
    "prov. bali": "bali",
    # NTB
    "nusa tenggara barat": "nusa_tenggara_barat",
    "ntb": "nusa_tenggara_barat",
    "prov. nusa tenggara barat": "nusa_tenggara_barat",
    # NTT
    "nusa tenggara timur": "nusa_tenggara_timur",
    "ntt": "nusa_tenggara_timur",
    "prov. nusa tenggara timur": "nusa_tenggara_timur",
    # Kalimantan Barat
    "kalimantan barat": "kalimantan_barat",
    "prov. kalimantan barat": "kalimantan_barat",
    "kalbar": "kalimantan_barat",
    # Kalimantan Tengah
    "kalimantan tengah": "kalimantan_tengah",
    "prov. kalimantan tengah": "kalimantan_tengah",
    "kalteng": "kalimantan_tengah",
    # Kalimantan Selatan
    "kalimantan selatan": "kalimantan_selatan",
    "prov. kalimantan selatan": "kalimantan_selatan",
    "kalsel": "kalimantan_selatan",
    # Kalimantan Timur
    "kalimantan timur": "kalimantan_timur",
    "prov. kalimantan timur": "kalimantan_timur",
    "kaltim": "kalimantan_timur",
    # Kalimantan Utara
    "kalimantan utara": "kalimantan_utara",
    "prov. kalimantan utara": "kalimantan_utara",
    "kaltara": "kalimantan_utara",
    # Sulawesi Utara
    "sulawesi utara": "sulawesi_utara",
    "prov. sulawesi utara": "sulawesi_utara",
    "sulut": "sulawesi_utara",
    # Sulawesi Tengah
    "sulawesi tengah": "sulawesi_tengah",
    "prov. sulawesi tengah": "sulawesi_tengah",
    "sulteng": "sulawesi_tengah",
    # Sulawesi Selatan
    "sulawesi selatan": "sulawesi_selatan",
    "prov. sulawesi selatan": "sulawesi_selatan",
    "sulsel": "sulawesi_selatan",
    # Sulawesi Tenggara
    "sulawesi tenggara": "sulawesi_tenggara",
    "prov. sulawesi tenggara": "sulawesi_tenggara",
    "sultra": "sulawesi_tenggara",
    # Gorontalo
    "gorontalo": "gorontalo",
    "prov. gorontalo": "gorontalo",
    # Sulawesi Barat
    "sulawesi barat": "sulawesi_barat",
    "prov. sulawesi barat": "sulawesi_barat",
    "sulbar": "sulawesi_barat",
    # Maluku
    "maluku": "maluku",
    "prov. maluku": "maluku",
    # Maluku Utara
    "maluku utara": "maluku_utara",
    "prov. maluku utara": "maluku_utara",
    "malut": "maluku_utara",
    # Papua
    "papua": "papua",
    "prov. papua": "papua",
    # Papua Barat
    "papua barat": "papua_barat",
    "prov. papua barat": "papua_barat",
}


def normalize_region(name: str) -> str | None:
    """Normalize nama wilayah ke slug dim_region.kode_wilayah. None jika unknown."""
    return REGION_NAME_TO_CODE.get(name.strip().lower())
