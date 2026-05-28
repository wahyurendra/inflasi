"""
Mapping nama wilayah dari berbagai sumber ke kode BPS.

Setiap sumber data bisa menggunakan nama wilayah yang berbeda.
Mapping ini menormalisasi semuanya ke kode BPS yang tersimpan di dim_region.
"""

# Mapping: variant nama → kode BPS
REGION_NAME_TO_CODE: dict[str, str] = {
    # Nasional
    "nasional": "00",
    "indonesia": "00",
    "national": "00",
    # Aceh
    "aceh": "11",
    "prov. aceh": "11",
    "nanggroe aceh darussalam": "11",
    "nad": "11",
    # Sumatera Utara
    "sumatera utara": "12",
    "prov. sumatera utara": "12",
    "sumut": "12",
    "sumatera utara (medan)": "12",
    # Sumatera Barat
    "sumatera barat": "13",
    "prov. sumatera barat": "13",
    "sumbar": "13",
    # Riau
    "riau": "14",
    "prov. riau": "14",
    # Jambi
    "jambi": "15",
    "prov. jambi": "15",
    # Sumatera Selatan
    "sumatera selatan": "16",
    "prov. sumatera selatan": "16",
    "sumsel": "16",
    # Bengkulu
    "bengkulu": "17",
    "prov. bengkulu": "17",
    # Lampung
    "lampung": "18",
    "prov. lampung": "18",
    # Kep. Bangka Belitung
    "kepulauan bangka belitung": "19",
    "bangka belitung": "19",
    "babel": "19",
    "kep. bangka belitung": "19",
    # Kep. Riau
    "kepulauan riau": "21",
    "kep. riau": "21",
    "kepri": "21",
    # DKI Jakarta
    "dki jakarta": "31",
    "prov. dki jakarta": "31",
    "jakarta": "31",
    # Jawa Barat
    "jawa barat": "32",
    "prov. jawa barat": "32",
    "jabar": "32",
    # Jawa Tengah
    "jawa tengah": "33",
    "prov. jawa tengah": "33",
    "jateng": "33",
    # DI Yogyakarta
    "di yogyakarta": "34",
    "d.i. yogyakarta": "34",
    "yogyakarta": "34",
    "diy": "34",
    "jogja": "34",
    # Jawa Timur
    "jawa timur": "35",
    "prov. jawa timur": "35",
    "jatim": "35",
    # Banten
    "banten": "36",
    "prov. banten": "36",
    # Bali
    "bali": "51",
    "prov. bali": "51",
    # NTB
    "nusa tenggara barat": "52",
    "ntb": "52",
    "prov. nusa tenggara barat": "52",
    # NTT
    "nusa tenggara timur": "53",
    "ntt": "53",
    "prov. nusa tenggara timur": "53",
    # Kalimantan Barat
    "kalimantan barat": "61",
    "prov. kalimantan barat": "61",
    "kalbar": "61",
    # Kalimantan Tengah
    "kalimantan tengah": "62",
    "prov. kalimantan tengah": "62",
    "kalteng": "62",
    # Kalimantan Selatan
    "kalimantan selatan": "63",
    "prov. kalimantan selatan": "63",
    "kalsel": "63",
    # Kalimantan Timur
    "kalimantan timur": "64",
    "prov. kalimantan timur": "64",
    "kaltim": "64",
    # Kalimantan Utara
    "kalimantan utara": "65",
    "prov. kalimantan utara": "65",
    "kaltara": "65",
    # Sulawesi Utara
    "sulawesi utara": "71",
    "prov. sulawesi utara": "71",
    "sulut": "71",
    # Sulawesi Tengah
    "sulawesi tengah": "72",
    "prov. sulawesi tengah": "72",
    "sulteng": "72",
    # Sulawesi Selatan
    "sulawesi selatan": "73",
    "prov. sulawesi selatan": "73",
    "sulsel": "73",
    # Sulawesi Tenggara
    "sulawesi tenggara": "74",
    "prov. sulawesi tenggara": "74",
    "sultra": "74",
    # Gorontalo
    "gorontalo": "75",
    "prov. gorontalo": "75",
    # Sulawesi Barat
    "sulawesi barat": "76",
    "prov. sulawesi barat": "76",
    "sulbar": "76",
    # Maluku
    "maluku": "81",
    "prov. maluku": "81",
    # Maluku Utara
    "maluku utara": "82",
    "prov. maluku utara": "82",
    "malut": "82",
    # Papua
    "papua": "91",
    "prov. papua": "91",
    # Papua Barat
    "papua barat": "92",
    "prov. papua barat": "92",
}


def normalize_region(name: str) -> str | None:
    """Normalize nama wilayah ke kode BPS. Returns None jika tidak ditemukan."""
    return REGION_NAME_TO_CODE.get(name.strip().lower())
