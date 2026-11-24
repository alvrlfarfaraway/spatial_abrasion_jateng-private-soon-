"""Luas daratan zona pesisir per kab/kota per tahun dari Landsat 8/9 (NDWI), via Google Earth Engine.

Persiapan sekali saja:
    pip install earthengine-api
    earthengine authenticate
Jalankan:
    python scripts/gee_luas_daratan_pesisir.py --project ID_PROYEK_GEE
Hasil:
    data/processed/luas_daratan_pesisir_jateng.csv  (kolom: nama_wilayah, tahun, luas_daratan_ha)
    data/processed/luas_zona_pesisir_per_kab.csv    (kolom: nama_wilayah, luas_zona_km2)
    outputs/cek_zona_pesisir_jateng.png             (peta cek kasar zona pesisir)

Dataset : FAO/GAUL/2025/level2 (kab/kota). Garis pantai dari GADM 4.1 lokal (mask darat),
          dibuat dulu oleh scripts/garis_pantai_lokal.py.
Zona    : buffer lebar_cincin_m (default 2000 m) ke darat dan ke laut dari garis pantai Jawa Tengah.
          Pita 30 m hanya untuk mencari garis, bukan lebar zona.
Daratan : piksel NDWI < ambang (default 0) di dalam zona, dijumlah per kab/kota, satuan hektar.
Ini proxy abrasi/akresi, bukan pengukuran langsung garis pantai.
"""
import argparse
import csv
import json
from pathlib import Path

import ee
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from shapely.geometry import shape  # noqa: E402

OUT = Path("data/processed/luas_daratan_pesisir_jateng.csv")
OUT_UJI = Path("data/processed/uji_pembanding_gabungan_pesisir.csv")  # hanya untuk --sensor gabungan
OUT_LUAS = Path("data/processed/luas_zona_pesisir_per_kab.csv")
OUT_PETA = Path("outputs/cek_zona_pesisir_jateng.png")
KOLEKSI_BATAS = "FAO/GAUL/2025/level2"
PROVINSI = "Jawa Tengah"
KOLOM_HASIL = "luas_ha"
GARIS_FILE = Path("data/processed/garis_pantai_jateng.geojson")  # dari scripts/garis_pantai_lokal.py


def komposit_tahunan(tahun, bulan_awal, bulan_akhir, wilayah, sensor="lc08"):
    """Komposit median per tahun. sensor 'lc08' untuk CSV utama, 'gabungan' (LC08 + LC09) hanya uji pembanding."""
    def siapkan(img):
        qa = img.select("QA_PIXEL")
        # bit 1 dilated cloud, 3 cloud, 4 cloud shadow
        mask = (
            qa.bitwiseAnd(1 << 1).eq(0)
            .And(qa.bitwiseAnd(1 << 3).eq(0))
            .And(qa.bitwiseAnd(1 << 4).eq(0))
        )
        sr = img.select(["SR_B3", "SR_B5"]).multiply(0.0000275).add(-0.2)
        return sr.rename(["hijau", "nir"]).updateMask(mask)

    awal = ee.Date.fromYMD(tahun, bulan_awal, 1)
    akhir = ee.Date.fromYMD(tahun, bulan_akhir, 1).advance(1, "month")  # eksklusif: sampai akhir bulan_akhir
    koleksi_lc08 = ee.ImageCollection("LANDSAT/LC08/C02/T1_L2")
    if sensor == "gabungan":
        koleksi_lc08 = koleksi_lc08.merge(ee.ImageCollection("LANDSAT/LC09/C02/T1_L2"))
    koleksi = koleksi_lc08.filterBounds(wilayah).filterDate(awal, akhir).map(siapkan)
    return koleksi.median().clip(wilayah)


def garis_pantai():
    """Garis pantai Jawa Tengah dari file lokal (GADM 4.1, mask darat).

    Dibuat oleh scripts/garis_pantai_lokal.py. Alasannya ada di docstring file itu.
    """
    if not GARIS_FILE.exists():
        raise SystemExit(f"{GARIS_FILE} belum ada. Jalankan scripts/garis_pantai_lokal.py dulu.")
    geom = json.loads(GARIS_FILE.read_text(encoding="utf-8"))["features"][0]["geometry"]
    return ee.Geometry(geom)


def simpan_luas_zona_per_kab(fitur_zona, garis, luas_total_km2):
    """Luas zona tiap kab/kota (km2) dan panjang garis pantai (km) untuk pengecekan.

    Jumlah luas per kab bisa lebih besar dari total karena buffer kab saling tumpang tindih.
    Panjang pantai = luas pita garis / 30 m (pita 30 m mengikuti garis pantai).
    """
    ringkas = fitur_zona.map(
        lambda f: ee.Feature(None, {
            "nama_wilayah": f.get("nama_wilayah"),
            "luas_zona_km2": f.geometry().area(1).divide(1e6),
        })
    )
    baris = sorted(
        (f["properties"] for f in ringkas.getInfo()["features"]),
        key=lambda b: b["nama_wilayah"],
    )
    OUT_LUAS.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_LUAS, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["nama_wilayah", "luas_zona_km2"])
        w.writeheader()
        for b in baris:
            w.writerow({"nama_wilayah": b["nama_wilayah"], "luas_zona_km2": round(b["luas_zona_km2"], 2)})

    jumlah = sum(b["luas_zona_km2"] for b in baris)
    panjang_km = garis.area(1).divide(30).divide(1000).getInfo()
    print("Luas zona per kab/kota (km2):")
    for b in baris:
        print(f"  {b['nama_wilayah']}: {b['luas_zona_km2']:.2f}")
    print("Jumlah per kab (km2):", round(jumlah, 2), "| total zona (km2):", round(luas_total_km2, 2))
    print("Panjang garis pantai perkiraan (km):", round(panjang_km, 1))
    print("Tersimpan:", OUT_LUAS)


def simpan_peta_cek(prov_geom, garis, zona):
    """Peta kasar untuk mengecek bahwa zona hanya menempel di garis pantai."""
    geo_prov = shape(prov_geom.simplify(200).getInfo())
    geo_garis = shape(garis.simplify(200).getInfo())
    geo_zona = shape(zona.simplify(200).getInfo())
    fig, ax = plt.subplots(figsize=(9, 7))
    for g, warna, alpha in [
        (geo_prov, "lightgrey", 1.0),
        (geo_zona, "tomato", 0.6),
        (geo_garis, "navy", 1.0),
    ]:
        for part in getattr(g, "geoms", [g]):
            if part.is_empty or part.geom_type != "Polygon":
                continue
            x, y = part.exterior.xy
            ax.fill(x, y, color=warna, alpha=alpha, linewidth=0)
    ax.set_title("Cek zona pesisir Jawa Tengah\n(merah: zona, biru: garis pantai, abu: provinsi)")
    ax.set_aspect("equal")
    ax.set_axis_off()
    OUT_PETA.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT_PETA, dpi=150, bbox_inches="tight")
    plt.close(fig)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--project", required=True, help="ID project Google Cloud untuk GEE")
    p.add_argument("--tahun_awal", type=int, default=2014)
    p.add_argument("--tahun_akhir", type=int, default=2025)
    p.add_argument("--bulan_awal", type=int, default=6, help="awal musim kemarau (kurangi awan)")
    p.add_argument("--bulan_akhir", type=int, default=10)
    p.add_argument("--lebar_cincin_m", type=int, default=2000,
                   help="lebar buffer ke darat dan ke laut dari garis pantai (meter), default 2 km")
    p.add_argument("--ambang_ndwi", type=float, default=0.0, help="NDWI < ambang dianggap daratan")
    p.add_argument("--sensor", choices=["lc08", "gabungan"], default="lc08",
                   help="lc08 untuk CSV utama. gabungan (LC08 + LC09) hanya uji pembanding, CSV terpisah")
    a = p.parse_args()
    keluaran = OUT if a.sensor == "lc08" else OUT_UJI

    ee.Initialize(project=a.project)

    kab = ee.FeatureCollection(KOLEKSI_BATAS).filter(ee.Filter.eq("GAUL1_NAME", PROVINSI))
    jumlah = kab.size().getInfo()
    print("Jumlah kab/kota di GAUL 2025:", jumlah, "(harapan 35)")
    if jumlah != 35:
        print("PERINGATAN: jumlah tidak 35. Cek daftar sebelum dipakai.")

    prov = kab.geometry().dissolve(maxError=100)
    garis = garis_pantai()
    zona = garis.buffer(a.lebar_cincin_m)
    luas_total_km2 = zona.area(1).divide(1e6).getInfo()
    print("Luas zona pesisir (km2):", round(luas_total_km2, 2))
    simpan_peta_cek(prov, garis, zona)
    print("Peta cek tersimpan:", OUT_PETA)

    # zona per kab/kota: buffer kab dipotong zona pesisir (batas antar kab boleh tumpang tindih kecil)
    fitur_zona = kab.map(
        lambda f: ee.Feature(
            f.geometry().buffer(a.lebar_cincin_m).intersection(zona, 100),
            {"nama_wilayah": f.get("GAUL2_NAME")},
        )
    )

    simpan_luas_zona_per_kab(fitur_zona, garis, luas_total_km2)

    keluaran.parent.mkdir(parents=True, exist_ok=True)
    reducer = ee.Reducer.sum().setOutputs([KOLOM_HASIL])
    baris = []
    kosong = 0
    for tahun in range(a.tahun_awal, a.tahun_akhir + 1):
        img = komposit_tahunan(tahun, a.bulan_awal, a.bulan_akhir, zona, sensor=a.sensor)
        ndwi = img.normalizedDifference(["hijau", "nir"])
        daratan = ndwi.lt(a.ambang_ndwi).selfMask().multiply(ee.Image.pixelArea()).divide(10000)
        hasil = daratan.rename(KOLOM_HASIL).reduceRegions(
            collection=fitur_zona, reducer=reducer, scale=30
        )
        fitur = hasil.getInfo()["features"]
        if tahun == a.tahun_awal and fitur:
            print("Contoh hasil mentah:", fitur[0]["properties"])
        for f in fitur:
            pr = f["properties"]
            if KOLOM_HASIL not in pr:
                raise SystemExit(f"Kolom '{KOLOM_HASIL}' tidak ada. Kunci yang ada: {sorted(pr)}")
            nilai = pr[KOLOM_HASIL]
            if nilai is None:
                kosong += 1
                nilai_csv = ""
            else:
                nilai_csv = round(nilai, 2)
            baris.append(
                {"nama_wilayah": pr["nama_wilayah"], "tahun": tahun, "luas_daratan_ha": nilai_csv}
            )
        print("selesai", tahun, flush=True)

    with open(keluaran, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["nama_wilayah", "tahun", "luas_daratan_ha"])
        w.writeheader()
        w.writerows(baris)
    print("Tersimpan:", keluaran, "| sensor:", a.sensor, "| baris:", len(baris), "| nilai kosong (None):", kosong)


if __name__ == "__main__":
    main()
