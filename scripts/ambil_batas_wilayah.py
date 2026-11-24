"""Unduh batas kab/kota Indonesia (GADM 4.1 level 2), saring Jawa Tengah.

Jalankan: python scripts/ambil_batas_wilayah.py
Hasil   : data/processed/batas_kabkota_jateng.geojson
Catatan : URL GADM belum diverifikasi dari sini. Kalau gagal, unduh manual dari gadm.org
          (negara Indonesia, level 2, format GeoJSON) ke data/raw/.
"""
import io
import sys
import zipfile
from pathlib import Path

import geopandas as gpd
import requests

URL = "https://geodata.ucdavis.edu/gadm/gadm4.1/json/gadm41_IDN_2.json.zip"
RAW = Path("data/raw")
OUT = Path("data/processed/batas_kabkota_jateng.geojson")


def main():
    RAW.mkdir(parents=True, exist_ok=True)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    zip_path = RAW / "gadm41_idn_2_json.zip"

    if not zip_path.exists():
        print("Mengunduh", URL)
        r = requests.get(URL, timeout=120, headers={"User-Agent": "tugas-kuliah-unnes/1.0"})
        r.raise_for_status()
        zip_path.write_bytes(r.content)

    with zipfile.ZipFile(zip_path) as z:
        nama = [n for n in z.namelist() if n.endswith(".json")][0]
        gdf = gpd.read_file(io.BytesIO(z.read(nama)))

    # GADM menulis nama provinsi tanpa spasi ("JawaTengah"), normalkan dulu
    kunci = gdf["NAME_1"].str.replace(" ", "", regex=False).str.lower()
    jateng = gdf[kunci == "jawatengah"].copy()
    if jateng.empty:
        print("Provinsi tidak ketemu. Nama yang ada:", sorted(gdf["NAME_1"].unique()))
        sys.exit(1)

    jateng = jateng[["GID_2", "NAME_2", "TYPE_2", "geometry"]].rename(
        columns={"GID_2": "kode_gadm", "NAME_2": "nama_wilayah", "TYPE_2": "tipe"}
    )
    jateng.to_file(OUT, driver="GeoJSON")
    print(f"Tersimpan: {OUT} ({len(jateng)} kab/kota). Harapannya 35.")


if __name__ == "__main__":
    main()
