"""Mapping nama komoditas dari berbagai sumber ke `dim_commodity.kode_komoditas`.

PIHPS BI uses specific variant names ("Beras Premium", "Beras Medium", "Cabai
Merah Besar", ...). We collapse them to the snake_case slugs the dimension
table actually stores, which mirror the codes already present in
`feature_store_daily`.
"""

COMMODITY_NAME_TO_CODE: dict[str, str] = {
    # Beras
    "beras": "beras",
    "beras premium": "beras",
    "beras medium": "beras",
    "beras kualitas bawah i": "beras",
    "beras kualitas bawah ii": "beras",
    "beras kualitas bawah iii": "beras",
    # Cabai Merah
    "cabai merah": "cabai_merah",
    "cabai merah besar": "cabai_merah",
    "cabai merah keriting": "cabai_merah",
    "cabe merah": "cabai_merah",
    "cabe merah besar": "cabai_merah",
    "cabe merah keriting": "cabai_merah",
    # Cabai Rawit
    "cabai rawit": "cabai_rawit",
    "cabai rawit merah": "cabai_rawit",
    "cabai rawit hijau": "cabai_rawit",
    "cabe rawit": "cabai_rawit",
    "cabe rawit merah": "cabai_rawit",
    "cabe rawit hijau": "cabai_rawit",
    # Bawang Merah
    "bawang merah": "bawang_merah",
    "bawang merah ukuran sedang": "bawang_merah",
    # Bawang Putih
    "bawang putih": "bawang_putih",
    "bawang putih ukuran sedang": "bawang_putih",
    "bawang putih bonggol": "bawang_putih",
    "bawang putih honan": "bawang_putih",
    # Telur Ayam Ras
    "telur ayam ras": "telur_ayam",
    "telur ayam": "telur_ayam",
    "telur ayam ras segar": "telur_ayam",
    # Daging Ayam Ras
    "daging ayam ras": "daging_ayam",
    "daging ayam": "daging_ayam",
    "daging ayam ras segar": "daging_ayam",
    "ayam ras": "daging_ayam",
    # Daging Sapi
    "daging sapi": "daging_sapi",
    "daging sapi murni": "daging_sapi",
    "daging sapi has": "daging_sapi",
    # Minyak Goreng (legacy — dimension currently does not include this slot;
    # left in the map so a future dim_commodity insert remains correct).
    "minyak goreng": "minyak_goreng",
    "minyak goreng curah": "minyak_goreng",
    "minyak goreng kemasan sederhana": "minyak_goreng",
    "minyak goreng kemasan bermerk 1": "minyak_goreng",
    "minyak goreng kemasan bermerk 2": "minyak_goreng",
    # Gula Pasir
    "gula pasir": "gula_pasir",
    "gula pasir lokal": "gula_pasir",
    "gula pasir premium": "gula_pasir",
    "gula pasir import": "gula_pasir",
    # Tepung Terigu
    "tepung terigu": "tepung_terigu_curah",
    "tepung terigu curah": "tepung_terigu_curah",
    "tepung terigu kemasan (curah)": "tepung_terigu_curah",
    "tepung terigu kemasan bermerek": "tepung_terigu_curah",
}

# Komoditas PIHPS BI yang dipilih sebagai representasi (jika ada multiple
# variant). Pilih yang paling umum / representatif.
PIHPS_PREFERRED_VARIANT: dict[str, str] = {
    "beras": "beras medium",
    "cabai_merah": "cabai merah besar",
    "cabai_rawit": "cabai rawit merah",
    "bawang_merah": "bawang merah",
    "bawang_putih": "bawang putih",
    "telur_ayam": "telur ayam ras",
    "daging_ayam": "daging ayam ras",
    "daging_sapi": "daging sapi",
    "minyak_goreng": "minyak goreng curah",
    "gula_pasir": "gula pasir lokal",
    "tepung_terigu_curah": "tepung terigu curah",
}


def normalize_commodity(name: str) -> str | None:
    """Normalize nama komoditas ke slug dim_commodity. None jika unknown."""
    return COMMODITY_NAME_TO_CODE.get(name.strip().lower())
