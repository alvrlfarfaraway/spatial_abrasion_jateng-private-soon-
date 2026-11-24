"""Garis pantai Jawa Tengah dari GADM 4.1 level 2 (lokal, data/raw), dipakai sebagai mask darat.

Mengapa lokal: batas provinsi GAUL 2025 menyisakan celah sekitar 1 km di batas Wonogiri dengan
DIY dan Jawa Timur. Celah itu dibaca sebagai laut. GADM memuat semua kabupaten/kota Indonesia,
sehingga daratan tetangga utuh.

Langkah:
  1. Pita 30 m di dalam batas luar Jawa Tengah.
  2. Buang bagian yang berbatasan dengan provinsi lain (buffer 100 m).
  3. Laut = cincin 2 km di luar Jawa Tengah, dikurangi daratan semua kabupaten/kota GADM.
     Buka morfologi 300 m untuk membuang sisa celah sempit.
  4. Garis pantai = pita di langkah 1-2 yang berjarak maksimal 300 m dari laut.

Jalankan: python scripts/garis_pantai_lokal.py
Hasil   : data/processed/garis_pantai_jateng.geojson (EPSG:4326, disederhanakan 15 m)
"""
import json
from pathlib import Path
import zipfile

import geopandas as gpd
from shapely.ops import unary_union

ZIP = Path("data/raw/gadm41_idn_2_json.zip")
OUT = Path("data/processed/garis_pantai_jateng.geojson")
PROVINSI = "JawaTengah"
EPSG_UTM = 32749  # UTM 49S, meter
LEBAR_LAUT_M = 2000
PITA_M = 30
BUFFER_PROVINSI_LAIN_M = 100
JENDELA_LAUT_M = 300
TOLERANSI_SEDERHANA_M = 15


def main():
    with zipfile.ZipFile(ZIP) as z:
        inner = [n for n in z.namelist() if n.endswith(".json")][0]
    gdf = gpd.read_file(f"zip://{ZIP.as_posix()}!{inner}").to_crs(EPSG_UTM)

    jateng = unary_union(gdf.loc[gdf["NAME_1"] == PROVINSI, "geometry"].values)
    darat_lain = unary_union(gdf.loc[gdf["NAME_1"] != PROVINSI, "geometry"].values)
    darat_semua = unary_union(gdf.geometry.values)

    pita = jateng.difference(jateng.buffer(-PITA_M)).difference(darat_lain.buffer(BUFFER_PROVINSI_LAIN_M))
    laut = jateng.buffer(LEBAR_LAUT_M).difference(jateng).difference(darat_semua)
    laut = laut.buffer(-JENDELA_LAUT_M).buffer(JENDELA_LAUT_M)
    garis = pita.intersection(laut.buffer(JENDELA_LAUT_M))

    panjang_km = garis.area / PITA_M / 1000
    print("Jumlah bagian garis:", len(getattr(garis, "geoms", [garis])))
    print("Panjang garis pantai perkiraan (km):", round(panjang_km, 1))

    garis_wgs = gpd.GeoSeries([garis.simplify(TOLERANSI_SEDERHANA_M, preserve_topology=True)],
                              crs=EPSG_UTM).to_crs(4326)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    gpd.GeoDataFrame({"nama": ["garis_pantai_jateng"]}, geometry=garis_wgs.values, crs=4326).to_file(
        OUT, driver="GeoJSON")
    fitur = json.loads(OUT.read_text(encoding="utf-8"))["features"][0]["geometry"]
    print("Tersimpan:", OUT, "| tipe:", fitur["type"], "| ukuran (byte):", OUT.stat().st_size)


if __name__ == "__main__":
    main()
