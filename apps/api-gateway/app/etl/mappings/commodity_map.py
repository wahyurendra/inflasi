"""
Mapping nama komoditas dari berbagai sumber ke kode internal.

PIHPS BI menggunakan nama spesifik (e.g. "Beras Premium", "Beras Medium").
Kita normalisasi ke 8 komoditas MVP.
"""

# Mapping: variant nama (lowercase) → kode komoditas internal
COMMODITY_NAME_TO_CODE: dict[str, str] = {
    # Beras
    "beras": "BERAS",
    "beras premium": "BERAS",
    "beras medium": "BERAS",
    "beras kualitas bawah i": "BERAS",
    "beras kualitas bawah ii": "BERAS",
    "beras kualitas bawah iii": "BERAS",
    # Cabai Merah
    "cabai merah": "CABAI_MERAH",
    "cabai merah besar": "CABAI_MERAH",
    "cabai merah keriting": "CABAI_MERAH",
    "cabe merah": "CABAI_MERAH",
    "cabe merah besar": "CABAI_MERAH",
    "cabe merah keriting": "CABAI_MERAH",
    # Cabai Rawit
    "cabai rawit": "CABAI_RAWIT",
    "cabai rawit merah": "CABAI_RAWIT",
    "cabai rawit hijau": "CABAI_RAWIT",
    "cabe rawit": "CABAI_RAWIT",
    "cabe rawit merah": "CABAI_RAWIT",
    "cabe rawit hijau": "CABAI_RAWIT",
    # Bawang Merah
    "bawang merah": "BAWANG_MERAH",
    "bawang merah ukuran sedang": "BAWANG_MERAH",
    # Bawang Putih
    "bawang putih": "BAWANG_PUTIH",
    "bawang putih ukuran sedang": "BAWANG_PUTIH",
    "bawang putih bonggol": "BAWANG_PUTIH",
    "bawang putih honan": "BAWANG_PUTIH",
    # Telur Ayam Ras
    "telur ayam ras": "TELUR_AYAM",
    "telur ayam": "TELUR_AYAM",
    "telur ayam ras segar": "TELUR_AYAM",
    # Minyak Goreng
    "minyak goreng": "MINYAK_GORENG",
    "minyak goreng curah": "MINYAK_GORENG",
    "minyak goreng kemasan sederhana": "MINYAK_GORENG",
    "minyak goreng kemasan bermerk 1": "MINYAK_GORENG",
    "minyak goreng kemasan bermerk 2": "MINYAK_GORENG",
    # Gula Pasir
    "gula pasir": "GULA_PASIR",
    "gula pasir lokal": "GULA_PASIR",
    "gula pasir premium": "GULA_PASIR",
    "gula pasir import": "GULA_PASIR",
}

# Komoditas PIHPS BI yang dipilih sebagai representasi (jika ada multiple variant)
# Pilih yang paling umum/representatif
PIHPS_PREFERRED_VARIANT: dict[str, str] = {
    "BERAS": "beras medium",
    "CABAI_MERAH": "cabai merah besar",
    "CABAI_RAWIT": "cabai rawit merah",
    "BAWANG_MERAH": "bawang merah",
    "BAWANG_PUTIH": "bawang putih",
    "TELUR_AYAM": "telur ayam ras",
    "MINYAK_GORENG": "minyak goreng curah",
    "GULA_PASIR": "gula pasir lokal",
}


def normalize_commodity(name: str) -> str | None:
    """Normalize nama komoditas ke kode internal. Returns None jika tidak ditemukan."""
    return COMMODITY_NAME_TO_CODE.get(name.strip().lower())
