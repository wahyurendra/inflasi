"""Blog Generator — turns the day's analytics into a public blog article.

Runs server-side as part of the daily analytics batch (run_analytics.py). Gathers
the same signals the dashboard shows (top commodities, pressure regions, alerts,
drivers), then asks OpenAI to write a journalistic Indonesian article in Markdown.
Falls back to a deterministic template when no OPENAI_API_KEY is configured, so the
batch never depends on an external API.

One row per (tanggal, tipe) — idempotent upsert.
"""

import json
import logging
import re
import unicodedata
from datetime import date, timedelta

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings

logger = logging.getLogger(__name__)

SOURCE_NOTE = "Sumber data: PIHPS Bank Indonesia, BPS."

# Minimum article length (words). The prompt + token budget target this.
MIN_WORDS = 1500
OPENAI_MAX_OUTPUT_TOKENS = 10000
OPENAI_REASONING_EFFORT = "low"

BLOG_ARTICLE_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["title", "excerpt", "tags", "body_md"],
    "properties": {
        "title": {"type": "string", "maxLength": 90},
        "excerpt": {"type": "string", "maxLength": 200},
        "tags": {
            "type": "array",
            "minItems": 4,
            "maxItems": 6,
            "items": {"type": "string"},
        },
        "body_md": {"type": "string"},
    },
}

# Canonical data sources. References for each article are assembled from the
# signals actually used, so citations stay grounded in real institutions.
SOURCES: dict[str, dict] = {
    "pihps": {"name": "PIHPS — Pusat Informasi Harga Pangan Strategis, Bank Indonesia", "url": "https://www.bi.go.id/hargapangan"},
    "bps": {"name": "Badan Pusat Statistik (BPS) — Data Inflasi & IHK", "url": "https://www.bps.go.id"},
    "bmkg": {"name": "BMKG — Badan Meteorologi, Klimatologi, dan Geofisika", "url": "https://www.bmkg.go.id"},
    "kurs": {"name": "Bank Indonesia — Kurs Referensi JISDOR", "url": "https://www.bi.go.id/id/statistik/informasi-kurs/jisdor/default.aspx"},
    "fao": {"name": "FAO Food Price Index — Food and Agriculture Organization", "url": "https://www.fao.org/worldfoodsituation/foodpricesindex"},
    "gscpi": {"name": "Federal Reserve Bank of New York — Global Supply Chain Pressure Index", "url": "https://www.newyorkfed.org/research/policy/gscpi"},
    "bapanas": {"name": "Badan Pangan Nasional (Bapanas) — Neraca & Stok Pangan", "url": "https://badanpangan.go.id"},
}

# Map a DriverAnalyzer factor name → the source key that backs it.
DRIVER_SOURCE = {
    "cuaca": "bmkg", "stok": "bapanas", "kurs": "kurs",
    "global": "fao", "logistik": "gscpi",
}

SYSTEM_PROMPT = f"""Kamu adalah jurnalis data senior untuk inflasi.id, platform pemantauan inflasi pangan Indonesia.
Tugasmu menulis SATU artikel blog harian yang KOMPREHENSIF dan mendalam berdasarkan HANYA data dalam tag <data>.

ATURAN KETAT (anti-halusinasi):
1. HANYA gunakan angka dan fakta dari tag <data>. JANGAN mengarang angka, harga, nama wilayah, atau sumber.
2. JANGAN membuat prediksi masa depan yang spesifik (angka) bila tidak ada di data; analisis outlook boleh tapi kualitatif dan hati-hati.
3. JANGAN mengarang penyebab tanpa indikator pendukung (driver) dari data.
4. Bahasa Indonesia jurnalistik yang mengalir, jelas, analitis, dan netral.
5. Format angka Indonesia (titik untuk ribuan, koma untuk desimal). Sertakan arah (naik/turun) + persentase pada setiap perubahan harga.
6. Sebutkan periode/tanggal data di awal artikel.

PANJANG & KEDALAMAN:
- Artikel WAJIB minimal {MIN_WORDS} kata. Tulis mendalam, jangan bertele-tele tetapi kaya konteks dan analisis.
- Struktur dengan banyak subjudul `## ` (dan `### ` bila perlu). Gunakan paragraf yang substantif, bukan hanya daftar.
- WAJIB mencakup bagian-bagian berikut (boleh menambah):
  1. Ringkasan eksekutif (gambaran besar hari ini).
  2. Sorotan inflasi nasional (MtM, YtD, YoY, IHK bila ada).
  3. Komoditas yang menanjak — bahas tiap komoditas teratas: harga, perubahan, dan implikasinya bagi konsumen.
  4. Komoditas yang melandai / stabil.
  5. Peta tekanan wilayah — provinsi dengan tekanan tertinggi dan konteksnya.
  6. Analisis faktor pendorong (driver): jelaskan kontribusi cuaca, stok, kurs, musiman, harga global, logistik berdasarkan data.
  7. Konteks global & makro (kurs USD/IDR, FAO Food Price Index, tekanan rantai pasok/GSCPI) bila tersedia.
  8. Volatilitas & disparitas harga antar wilayah (bila tersedia).
  9. Implikasi & outlook kualitatif untuk pemerintah daerah, pelaku usaha, dan konsumen.
  10. Catatan metodologi singkat (bagaimana angka dihitung & keterbatasannya).
  11. Bagian `## Referensi` — daftar sumber dari field `references` di <data>, ditulis sebagai tautan Markdown `[Nama](url)`.

Kembalikan JSON valid dengan struktur PERSIS:
{{
  "title": "judul menarik & spesifik (maks 90 karakter)",
  "excerpt": "ringkasan 1-2 kalimat untuk meta description (maks 200 karakter)",
  "tags": ["4-6 tag relevan: nama komoditas/wilayah/tema"],
  "body_md": "isi artikel Markdown minimal {MIN_WORDS} kata, tanpa judul H1, diakhiri bagian ## Referensi"
}}"""


def slugify(value: str) -> str:
    value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    value = re.sub(r"[^\w\s-]", "", value.lower()).strip()
    value = re.sub(r"[\s_-]+", "-", value)
    return value[:180].strip("-") or "artikel"


class BlogGenerator:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ── Public API ────────────────────────────────────────────

    async def generate(self, tanggal: date, tipe: str = "harian") -> dict:
        """Gather → narrate (OpenAI or fallback) → upsert. Returns the post dict."""
        data = await self.gather(tanggal)

        article: dict | None = None
        model_used = "template"
        if settings.openai_api_key:
            try:
                article = await self._call_openai(data)
                model_used = settings.openai_model
            except Exception as exc:  # noqa: BLE001 — never fail the batch on LLM error
                logger.warning("OpenAI blog generation failed (%s); using template", exc)

        if not article:
            article = self._fallback(data)

        title = (article.get("title") or f"Pantauan Harga Pangan {tanggal.isoformat()}").strip()
        excerpt = (article.get("excerpt") or "").strip()[:400]
        body_md = (article.get("body_md") or "").strip()
        tags = article.get("tags") or data.get("tags") or []
        slug = f"{slugify(title)}-{tanggal.isoformat()}"

        await self._upsert(
            tanggal=tanggal, tipe=tipe, slug=slug, title=title[:200],
            excerpt=excerpt, body_md=body_md, tags=tags,
            data_snapshot=data, model=model_used,
        )
        logger.info("Blog post upserted: %s (%s)", slug, model_used)
        return {
            "slug": slug, "title": title, "excerpt": excerpt,
            "tanggal": tanggal.isoformat(), "tipe": tipe, "model": model_used,
        }

    async def list_published(self, limit: int = 20, offset: int = 0) -> list[dict]:
        result = await self.db.execute(
            text("""
                SELECT slug, title, excerpt, tipe, tanggal, published_at, tags
                FROM content_blog_posts
                WHERE status = 'published'
                ORDER BY published_at DESC NULLS LAST, tanggal DESC
                LIMIT :limit OFFSET :offset
            """),
            {"limit": limit, "offset": offset},
        )
        return [self._row_dict(r) for r in result.fetchall()]

    async def get_by_slug(self, slug: str) -> dict | None:
        result = await self.db.execute(
            text("""
                SELECT slug, title, excerpt, body_md, tipe, tanggal, published_at, tags
                FROM content_blog_posts
                WHERE slug = :slug AND status = 'published'
            """),
            {"slug": slug},
        )
        row = result.fetchone()
        return self._row_dict(row) if row else None

    # ── Data gathering ────────────────────────────────────────

    async def gather(self, tanggal: date) -> dict:
        """Collect the day's analytical material (mirrors InsightGenerator queries)."""
        # Headline inflation (latest national row at/before tanggal)
        headline_q = await self.db.execute(
            text("""
                SELECT periode,
                       MAX(inflasi_mtm) AS mtm,
                       MAX(inflasi_ytd) AS ytd,
                       MAX(inflasi_yoy) AS yoy,
                       MAX(ihk) AS ihk
                FROM fact_inflation_monthly
                WHERE (kelompok IS NULL OR kelompok = 'umum') AND commodity_id IS NULL
                GROUP BY periode
                ORDER BY periode DESC
                LIMIT 1
            """)
        )
        h = headline_q.fetchone()
        headline = (
            {
                "periode": h.periode.isoformat() if h and h.periode else None,
                "mtm": float(h.mtm) if h and h.mtm is not None else None,
                "ytd": float(h.ytd) if h and h.ytd is not None else None,
                "yoy": float(h.yoy) if h and h.yoy is not None else None,
                "ihk": float(h.ihk) if h and h.ihk is not None else None,
            }
            if h else None
        )

        # Top rising / falling commodities
        comm_q = await self.db.execute(
            text("""
                SELECT dc.nama_display AS nama, dc.kode_komoditas AS kode,
                       ROUND(AVG(fpd.perubahan_mingguan)::numeric, 1) AS weekly,
                       ROUND(AVG(fpd.harga)::numeric, 0) AS harga
                FROM fact_price_daily fpd
                JOIN dim_commodity dc ON dc.id = fpd.commodity_id
                WHERE fpd.tanggal = :tanggal
                GROUP BY dc.nama_display, dc.kode_komoditas
                HAVING AVG(fpd.perubahan_mingguan) IS NOT NULL
                ORDER BY weekly DESC
            """),
            {"tanggal": tanggal},
        )
        comms = [
            {"nama": r.nama, "kode": r.kode,
             "weekly": float(r.weekly) if r.weekly is not None else 0.0,
             "harga": float(r.harga) if r.harga is not None else None}
            for r in comm_q.fetchall()
        ]
        top_rising = [c for c in comms if c["weekly"] > 0][:3]
        top_falling = [c for c in reversed(comms) if c["weekly"] < 0][:3]

        # Top pressure provinces
        reg_q = await self.db.execute(
            text("""
                SELECT dr.nama_provinsi AS nama,
                       ROUND(AVG(fpd.perubahan_mingguan)::numeric, 1) AS weekly
                FROM fact_price_daily fpd
                JOIN dim_region dr ON dr.id = fpd.region_id
                WHERE fpd.tanggal = :tanggal AND dr.level_wilayah = 'provinsi'
                GROUP BY dr.nama_provinsi
                HAVING AVG(fpd.perubahan_mingguan) IS NOT NULL
                ORDER BY weekly DESC
                LIMIT 5
            """),
            {"tanggal": tanggal},
        )
        regions = [
            {"nama": r.nama, "weekly": float(r.weekly) if r.weekly is not None else 0.0}
            for r in reg_q.fetchall()
        ]

        # Active alerts
        alert_count_q = await self.db.execute(
            text("SELECT COUNT(*) AS cnt FROM analytics_alerts WHERE is_active = TRUE")
        )
        alert_count = alert_count_q.scalar() or 0
        alert_rows_q = await self.db.execute(
            text("""
                SELECT severity, judul, deskripsi
                FROM analytics_alerts
                WHERE is_active = TRUE
                ORDER BY CASE severity WHEN 'critical' THEN 0 WHEN 'warning' THEN 1 ELSE 2 END
                LIMIT 5
            """)
        )
        alerts = [
            {"severity": r.severity, "judul": r.judul, "deskripsi": r.deskripsi}
            for r in alert_rows_q.fetchall()
        ]

        # Drivers for the #1 rising commodity (best-effort, national region).
        # Savepoint-isolated so a failure inside DriverAnalyzer can't poison the
        # outer transaction (which would block the final upsert).
        drivers: list[dict] = []
        driver_commodity = top_rising[0]["nama"] if top_rising else None
        if top_rising:
            try:
                async with self.db.begin_nested():
                    ids_q = await self.db.execute(
                        text("""
                            SELECT (SELECT id FROM dim_commodity WHERE kode_komoditas = :kode) AS cid,
                                   (SELECT id FROM dim_region
                                    WHERE level_wilayah = 'nasional' ORDER BY id LIMIT 1) AS rid
                        """),
                        {"kode": top_rising[0]["kode"]},
                    )
                    ids = ids_q.fetchone()
                    if ids and ids.cid and ids.rid:
                        from app.services.driver_analyzer import DriverAnalyzer
                        res = await DriverAnalyzer(self.db).analyze(ids.cid, ids.rid, tanggal)
                        drivers = [
                            {"name": d.get("name"), "contribution_pct": d.get("contribution_pct"),
                             "direction": d.get("direction"), "detail": d.get("detail")}
                            for d in (res.get("drivers") or [])[:3]
                        ]
            except Exception as exc:  # noqa: BLE001
                logger.debug("driver analysis skipped: %s", exc)

        # Global / macro context (best-effort; tables may be empty)
        kurs = await self._scalar_row(
            "SELECT tanggal, kurs_tengah, change_pct FROM ext_exchange_rate "
            "ORDER BY tanggal DESC LIMIT 1",
            lambda r: {
                "tanggal": r.tanggal.isoformat() if r.tanggal else None,
                "kurs_tengah": float(r.kurs_tengah) if r.kurs_tengah is not None else None,
                "change_pct": float(r.change_pct) if r.change_pct is not None else None,
            },
        )
        fao = await self._scalar_row(
            "SELECT periode, index_overall FROM ext_fao_food_price "
            "ORDER BY periode DESC LIMIT 1",
            lambda r: {
                "periode": r.periode.isoformat() if r.periode else None,
                "index_overall": float(r.index_overall) if r.index_overall is not None else None,
            },
        )
        gscpi = await self._scalar_row(
            "SELECT periode, gscpi FROM ext_supply_chain_index "
            "ORDER BY periode DESC LIMIT 1",
            lambda r: {
                "periode": r.periode.isoformat() if r.periode else None,
                "gscpi": float(r.gscpi) if r.gscpi is not None else None,
            },
        )

        # Volatility leaders (CV of harga over the last 30 days). `since` is
        # computed in Python to avoid a `::date` cast adjacent to a named param
        # (which collides with SQLAlchemy's text() param parsing).
        volatility: list[dict] = []
        try:
            async with self.db.begin_nested():
                vol_q = await self.db.execute(
                    text("""
                        SELECT dc.nama_display AS nama,
                               ROUND((STDDEV_SAMP(fpd.harga) / NULLIF(AVG(fpd.harga), 0) * 100)::numeric, 1) AS cv
                        FROM fact_price_daily fpd
                        JOIN dim_commodity dc ON dc.id = fpd.commodity_id
                        WHERE fpd.tanggal > :since AND fpd.tanggal <= :tanggal
                        GROUP BY dc.nama_display
                        HAVING COUNT(*) >= 5
                        ORDER BY cv DESC NULLS LAST
                        LIMIT 5
                    """),
                    {"tanggal": tanggal, "since": tanggal - timedelta(days=30)},
                )
                volatility = [
                    {"nama": r.nama, "cv": float(r.cv) if r.cv is not None else None}
                    for r in vol_q.fetchall()
                ]
        except Exception as exc:  # noqa: BLE001
            logger.debug("volatility skipped: %s", exc)

        # Build references from the signals actually used.
        ref_keys: list[str] = ["pihps", "bps"]
        for d in drivers:
            key = DRIVER_SOURCE.get((d.get("name") or "").lower())
            if key:
                ref_keys.append(key)
        if kurs:
            ref_keys.append("kurs")
        if fao:
            ref_keys.append("fao")
        if gscpi:
            ref_keys.append("gscpi")
        seen: set[str] = set()
        references = [
            SOURCES[k] for k in ref_keys
            if k in SOURCES and not (k in seen or seen.add(k))
        ]

        tags = list({c["nama"] for c in top_rising} | {"inflasi pangan", "harga pangan"})

        return {
            "tanggal": tanggal.isoformat(),
            "headline": headline,
            "top_rising": top_rising,
            "top_falling": top_falling,
            "regions": regions,
            "alert_count": alert_count,
            "alerts": alerts,
            "driver_commodity": driver_commodity,
            "drivers": drivers,
            "kurs": kurs,
            "fao": fao,
            "gscpi": gscpi,
            "volatility": volatility,
            "references": references,
            "tags": tags[:6],
        }

    async def _scalar_row(self, sql: str, mapper):
        """Run a single-row best-effort query in a SAVEPOINT so a failure (e.g.
        missing table) rolls back only this query, never the outer transaction."""
        try:
            async with self.db.begin_nested():
                res = await self.db.execute(text(sql))
                row = res.fetchone()
            return mapper(row) if row else None
        except Exception as exc:  # noqa: BLE001
            logger.debug("context query skipped (%s): %s", sql[:40], exc)
            return None

    # ── OpenAI ────────────────────────────────────────────────

    async def _call_openai(self, data: dict) -> dict:
        from openai import AsyncOpenAI

        client = AsyncOpenAI(api_key=settings.openai_api_key)
        user_prompt = (
            f"Tanggal data: {data['tanggal']}\n\n"
            f"<data>\n{json.dumps(data, ensure_ascii=False, indent=2)}\n</data>\n\n"
            f"Tulis artikel blog harian yang komprehensif (MINIMAL {MIN_WORDS} kata) "
            "berdasarkan data di atas, mengikuti seluruh bagian yang diminta dan "
            "diakhiri bagian '## Referensi' yang memuat setiap sumber dari field "
            "`references` sebagai tautan Markdown. Kembalikan HANYA JSON sesuai struktur."
        )
        resp = await self._create_blog_article_response(client, user_prompt)
        content = self._response_output_text(resp) or "{}"
        article = json.loads(content)
        if not article.get("body_md"):
            raise ValueError("empty body_md from OpenAI")

        # If the draft is under the minimum, ask once to expand it.
        if len(article["body_md"].split()) < MIN_WORDS:
            expand_prompt = (
                f"{user_prompt}\n\n"
                f"<draft_json>\n{content}\n</draft_json>\n\n"
                f"Artikel dalam draft masih di bawah {MIN_WORDS} kata. Perluas menjadi "
                f"MINIMAL {MIN_WORDS} kata dengan memperdalam analisis di setiap bagian "
                "(tambah konteks, implikasi, dan penjelasan), TANPA mengarang angka baru "
                "dan tanpa mengulang kalimat. Kembalikan JSON penuh yang sama."
            )
            try:
                resp2 = await self._create_blog_article_response(client, expand_prompt)
                article2 = json.loads(self._response_output_text(resp2) or "{}")
                if article2.get("body_md") and len(article2["body_md"].split()) > len(article["body_md"].split()):
                    article = article2
            except Exception as exc:  # noqa: BLE001
                logger.debug("expand retry failed: %s", exc)

        body = article["body_md"]
        # Guarantee a references section even if the model omitted it.
        if "## Referensi" not in body and "## referensi" not in body.lower():
            body = body.rstrip() + "\n\n" + self._references_md(data)
        # Provenance footer.
        if SOURCE_NOTE.split(":")[0] not in body:
            body += f"\n\n_{SOURCE_NOTE}_"
        article["body_md"] = body
        return article

    async def _create_blog_article_response(self, client, user_prompt: str):
        return await client.responses.create(
            model=settings.openai_model,
            instructions=SYSTEM_PROMPT,
            input=user_prompt,
            text={
                "format": {
                    "type": "json_schema",
                    "name": "blog_article",
                    "schema": BLOG_ARTICLE_SCHEMA,
                    "strict": True,
                },
                "verbosity": "high",
            },
            reasoning={"effort": OPENAI_REASONING_EFFORT},
            temperature=0.7,
            max_output_tokens=OPENAI_MAX_OUTPUT_TOKENS,
            store=False,
        )

    @staticmethod
    def _response_output_text(resp) -> str:
        content = getattr(resp, "output_text", None)
        if content:
            return content

        parts: list[str] = []
        for item in getattr(resp, "output", []) or []:
            for part in getattr(item, "content", []) or []:
                text = getattr(part, "text", None)
                if text:
                    parts.append(text)
                elif isinstance(part, dict) and part.get("text"):
                    parts.append(part["text"])
        return "".join(parts)

    @staticmethod
    def _references_md(data: dict) -> str:
        refs = data.get("references") or [SOURCES["pihps"], SOURCES["bps"]]
        lines = ["## Referensi", ""]
        lines += [f"- [{r['name']}]({r['url']})" for r in refs]
        return "\n".join(lines)

    # ── Deterministic fallback ────────────────────────────────

    def _fallback(self, data: dict) -> dict:
        """Comprehensive deterministic article (used when OpenAI is unavailable)."""
        tgl = date.fromisoformat(data["tanggal"]).strftime("%d %B %Y")
        title = f"Pantauan Harga Pangan Nasional — {tgl}"
        rising = data.get("top_rising") or []
        falling = data.get("top_falling") or []
        regions = data.get("regions") or []
        L: list[str] = []

        def rp(v) -> str:
            return f"Rp{v:,.0f}".replace(",", ".") if v else "-"

        # 1. Ringkasan eksekutif
        L += ["## Ringkasan Eksekutif", ""]
        lead = rising[0]["nama"] if rising else None
        L.append(
            f"Laporan pemantauan harga pangan nasional untuk **{tgl}** ini merangkum "
            "pergerakan harga komoditas pangan strategis di seluruh Indonesia, tekanan "
            "harga di tingkat provinsi, faktor-faktor pendorong, serta konteks makro dan "
            "global yang relevan. Data dihimpun dari Pusat Informasi Harga Pangan "
            "Strategis (PIHPS) Bank Indonesia dan Badan Pusat Statistik (BPS), kemudian "
            "diolah oleh mesin analitik inflasi.id."
        )
        if lead:
            L.append(
                f"Pada periode ini, **{lead}** menjadi komoditas dengan tekanan kenaikan "
                f"tertinggi, naik **{abs(rising[0]['weekly'])}%** secara mingguan. "
                + (f"Secara keseluruhan terdapat **{data['alert_count']} alert aktif** "
                   "yang memerlukan perhatian pemangku kepentingan."
                   if data.get("alert_count") else "")
            )
        L.append("")

        # 2. Sorotan inflasi nasional
        h = data.get("headline")
        if h:
            L += ["## Sorotan Inflasi Nasional", ""]
            L.append(
                f"Berdasarkan rilis BPS periode {h.get('periode')}, inflasi umum tercatat "
                f"**{(h.get('mtm') or 0):+.2f}% (month-to-month)**, "
                f"**{(h.get('ytd') or 0):+.2f}% (year-to-date)**, dan "
                f"**{(h.get('yoy') or 0):+.2f}% (year-on-year)**"
                + (f", dengan Indeks Harga Konsumen (IHK) di level {h.get('ihk')}." if h.get('ihk') else ".")
            )
            L.append(
                "Inflasi month-to-month menggambarkan tekanan harga jangka pendek, "
                "sementara angka year-on-year memberi gambaran tren struktural dibanding "
                "periode yang sama tahun sebelumnya. Komponen bahan pangan kerap menjadi "
                "penyumbang utama volatilitas inflasi di Indonesia."
            )
            L.append("")

        # 3. Komoditas menanjak
        if rising:
            L += ["## Komoditas yang Menanjak", ""]
            L.append(
                "Berikut komoditas dengan kenaikan harga mingguan tertinggi. Kenaikan "
                "yang persisten pada komoditas bumbu dan protein cenderung paling cepat "
                "memukul daya beli rumah tangga berpendapatan rendah, karena kelompok ini "
                "memiliki porsi pengeluaran pangan yang besar terhadap total pendapatan."
            )
            L.append("")
            for c in rising:
                pct = abs(c["weekly"])
                tone = (
                    "lonjakan yang signifikan dan perlu diwaspadai" if pct >= 10
                    else "kenaikan yang cukup terasa" if pct >= 5
                    else "kenaikan moderat"
                )
                L += [f"### {c['nama']}", ""]
                L.append(
                    f"Harga rata-rata **{c['nama']}** tercatat **{rp(c.get('harga'))}/kg**, "
                    f"naik **{pct}%** secara mingguan — {tone}. Pergerakan ini berkontribusi "
                    "langsung pada beban belanja pangan harian rumah tangga. Bagi pedagang "
                    "dan pelaku UMKM kuliner, kenaikan biaya bahan baku ini berpotensi "
                    "menekan margin atau mendorong penyesuaian harga jual di tingkat akhir."
                )
                L.append("")

        # 4. Komoditas melandai
        if falling:
            L += ["## Komoditas yang Melandai", ""]
            names = ", ".join(f"**{c['nama']}**" for c in falling)
            L.append(
                f"Di sisi lain, sejumlah komoditas — yakni {names} — mencatat penurunan "
                "harga dalam sepekan terakhir, memberi ruang lega bagi anggaran belanja "
                "rumah tangga. Penurunan harga umumnya didorong oleh membaiknya pasokan, "
                "masuknya musim panen, atau normalisasi setelah lonjakan sebelumnya."
            )
            for c in falling:
                L.append(
                    f"- **{c['nama']}** turun **{abs(c['weekly'])}%** secara mingguan, "
                    "mengindikasikan tekanan harga yang mereda untuk komoditas ini."
                )
            L.append("")

        # 5. Peta tekanan wilayah
        if regions:
            L += ["## Peta Tekanan Wilayah", ""]
            L.append(
                "Tekanan harga tidak merata secara geografis. Perbedaan kondisi pasokan, "
                "biaya logistik, dan pola konsumsi membuat sejumlah provinsi menanggung "
                "kenaikan harga yang lebih tinggi dari rata-rata nasional. Provinsi berikut "
                "perlu menjadi prioritas pemantauan Tim Pengendalian Inflasi Daerah (TPID):"
            )
            for i, r in enumerate(regions[:5], 1):
                L.append(
                    f"{i}. **{r['nama']}** — rata-rata kenaikan harga {r['weekly']}% "
                    "di seluruh komoditas terpantau."
                )
            top_region = regions[0]
            L.append("")
            L.append(
                f"**{top_region['nama']}** berada di puncak daftar dengan rata-rata "
                f"kenaikan {top_region['weekly']}%. Konsentrasi tekanan di satu wilayah "
                "biasanya menjadi sinyal awal untuk mempersiapkan operasi pasar atau "
                "memperlancar arus distribusi dari daerah surplus terdekat."
            )
            L.append("")

        # 6. Faktor pendorong
        if data.get("drivers") and data.get("driver_commodity"):
            L += [f"## Analisis Faktor Pendorong — {data['driver_commodity']}", ""]
            L.append(
                "Analisis driver mengurai kontribusi relatif dari berbagai faktor "
                "terhadap pergerakan harga komoditas dengan tekanan tertinggi:"
            )
            for d in data["drivers"]:
                name = (d.get("name") or "").title()
                pct = d.get("contribution_pct")
                detail = d.get("detail") or ""
                pct_s = f" (~{pct}%)" if pct is not None else ""
                L.append(f"- **{name}**{pct_s}: {detail}")
            L.append("")

        # 7. Konteks global & makro
        kurs, fao, gscpi = data.get("kurs"), data.get("fao"), data.get("gscpi")
        if kurs or fao or gscpi:
            L += ["## Konteks Global & Makro", ""]
            if kurs and kurs.get("kurs_tengah"):
                L.append(
                    f"Nilai tukar rupiah berada di **Rp{kurs['kurs_tengah']:,.0f}**".replace(",", ".")
                    + f"/USD (JISDOR, {kurs.get('tanggal')})"
                    + (f", bergerak {kurs['change_pct']:+.2f}% dibanding sebelumnya. "
                       if kurs.get("change_pct") is not None else ". ")
                    + "Pelemahan rupiah menambah beban komoditas impor seperti bawang "
                    "putih, gula, dan kedelai."
                )
            if fao and fao.get("index_overall"):
                L.append(
                    f"FAO Food Price Index global tercatat **{fao['index_overall']}** "
                    f"(periode {fao.get('periode')}), menjadi indikator arah harga pangan dunia."
                )
            if gscpi and gscpi.get("gscpi") is not None:
                L.append(
                    f"Global Supply Chain Pressure Index (GSCPI) berada di **{gscpi['gscpi']}** "
                    f"(periode {gscpi.get('periode')}); nilai di atas nol menandakan tekanan "
                    "rantai pasok global di atas rata-rata historis."
                )
            L.append("")

        # 8. Volatilitas
        vol = data.get("volatility") or []
        if vol:
            L += ["## Volatilitas Harga", ""]
            L.append(
                "Volatilitas diukur dengan koefisien variasi (CV) harga 30 hari terakhir. "
                "Semakin tinggi CV, semakin tidak stabil harga komoditas tersebut:"
            )
            for v in vol[:5]:
                if v.get("cv") is not None:
                    L.append(f"- **{v['nama']}** — CV {v['cv']}%.")
            L.append("")

        # 9. Implikasi & outlook
        L += ["## Implikasi & Outlook", ""]
        L.append(
            "Bagi **pemerintah daerah**, data ini menjadi sinyal dini untuk operasi pasar "
            "dan koordinasi pasokan di wilayah dengan tekanan tertinggi. Bagi **pelaku "
            "usaha dan UMKM pangan**, pergerakan harga membantu perencanaan stok dan "
            "penetapan harga. Bagi **konsumen**, informasi ini berguna untuk menyesuaikan "
            "pola belanja terhadap komoditas yang sedang naik."
        )
        L.append(
            "Arah harga ke depan akan sangat dipengaruhi oleh faktor cuaca terhadap "
            "produksi, kelancaran distribusi antarwilayah, serta dinamika nilai tukar dan "
            "harga komoditas global. Pemantauan harian diperlukan karena harga pangan "
            "dapat bergerak lebih cepat daripada siklus pelaporan resmi."
        )
        L.append("")

        # 10. Cara membaca indikator
        L += ["## Cara Membaca Indikator", ""]
        L.append(
            "Perubahan **mingguan** paling relevan untuk menangkap tekanan jangka pendek "
            "akibat gangguan pasokan atau lonjakan permintaan musiman, sementara perubahan "
            "**bulanan** membantu memisahkan tren dari fluktuasi harian. Untuk komoditas "
            "bumbu seperti cabai dan bawang, volatilitas tinggi adalah hal yang lumrah "
            "karena sifat produksinya yang musiman dan mudah rusak (perishable). "
            "Sebaliknya, kestabilan harga beras menjadi indikator penting ketahanan pangan "
            "karena bobotnya yang besar dalam keranjang konsumsi rumah tangga Indonesia."
        )
        L.append(
            "Disparitas harga antarwilayah sering kali mencerminkan biaya logistik dan "
            "ketimpangan pasokan, bukan semata perbedaan permintaan. Wilayah dengan "
            "infrastruktur distribusi terbatas cenderung menanggung harga yang lebih "
            "tinggi dan lebih bergejolak."
        )
        L.append("")

        # 11. Glosarium
        L += ["## Glosarium Singkat", ""]
        L += [
            "- **MtM (month-to-month)**: perubahan harga/indeks dibanding bulan sebelumnya.",
            "- **YoY (year-on-year)**: perubahan dibanding periode yang sama tahun lalu.",
            "- **IHK**: Indeks Harga Konsumen, ukuran rata-rata harga keranjang konsumsi.",
            "- **CV (coefficient of variation)**: ukuran volatilitas; makin tinggi makin tidak stabil.",
            "- **GSCPI**: indeks tekanan rantai pasok global dari Fed New York.",
            "- **TPID**: Tim Pengendalian Inflasi Daerah di tingkat provinsi/kabupaten/kota.",
        ]
        L.append("")

        # 12. Metodologi
        L += ["## Catatan Metodologi", ""]
        L.append(
            "Perubahan harga dihitung sebagai persentase terhadap harga pada periode "
            "pembanding (harian, mingguan, bulanan) dari data PIHPS. Tekanan wilayah "
            "merupakan rata-rata perubahan mingguan seluruh komoditas terpantau di "
            "provinsi terkait. Analisis driver menggunakan pendekatan weighted heuristic "
            "atas sinyal cuaca, stok, kurs, musiman, harga global, dan logistik. Angka "
            "bersifat indikatif dan dapat direvisi seiring pemutakhiran data sumber. "
            "Laporan ini dihasilkan secara otomatis oleh sistem analitik inflasi.id dan "
            "ditujukan sebagai alat bantu pemantauan, bukan pengganti rilis statistik resmi."
        )
        L.append("")

        # 13. Referensi
        L.append(self._references_md(data))
        L.append("")
        L.append(f"_{SOURCE_NOTE}_")

        excerpt = (
            f"Analisis harga pangan {tgl}: "
            + (f"{rising[0]['nama']} memimpin kenaikan {abs(rising[0]['weekly'])}%. " if rising else "")
            + (f"{data['alert_count']} alert aktif. " if data.get("alert_count") else "")
            + "Lengkap dengan faktor pendorong, konteks global, dan referensi."
        )
        return {
            "title": title,
            "excerpt": excerpt[:400],
            "tags": data.get("tags") or ["inflasi pangan", "harga pangan"],
            "body_md": "\n".join(L),
        }

    # ── Persistence ───────────────────────────────────────────

    async def _upsert(
        self, *, tanggal: date, tipe: str, slug: str, title: str, excerpt: str,
        body_md: str, tags: list, data_snapshot: dict, model: str,
    ) -> None:
        await self.db.execute(
            text("""
                INSERT INTO content_blog_posts
                    (slug, title, excerpt, body_md, tipe, status, tanggal,
                     published_at, tags, data_snapshot, model, updated_at)
                VALUES
                    (:slug, :title, :excerpt, :body_md, :tipe, 'published', :tanggal,
                     NOW(), CAST(:tags AS jsonb), CAST(:snapshot AS jsonb), :model, NOW())
                ON CONFLICT (tanggal, tipe) DO UPDATE SET
                    slug = EXCLUDED.slug,
                    title = EXCLUDED.title,
                    excerpt = EXCLUDED.excerpt,
                    body_md = EXCLUDED.body_md,
                    tags = EXCLUDED.tags,
                    data_snapshot = EXCLUDED.data_snapshot,
                    model = EXCLUDED.model,
                    published_at = EXCLUDED.published_at,
                    updated_at = NOW()
            """),
            {
                "slug": slug, "title": title, "excerpt": excerpt, "body_md": body_md,
                "tipe": tipe, "tanggal": tanggal,
                "tags": json.dumps(tags, ensure_ascii=False),
                "snapshot": json.dumps(data_snapshot, ensure_ascii=False),
                "model": model,
            },
        )
        await self.db.commit()

    @staticmethod
    def _row_dict(row) -> dict:
        d = dict(row._mapping)
        if d.get("tanggal"):
            d["tanggal"] = d["tanggal"].isoformat()
        if d.get("published_at"):
            d["published_at"] = d["published_at"].isoformat()
        return d
