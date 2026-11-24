"""Peta choropleth dan Moran's I global untuk rata-rata PM2.5 SIMULASI per kab/kota Jawa Tengah.

Jalankan: python scripts/simulasi_peta_dan_moran.py
Masukan : data/processed/simulasi_pm25_jateng_panel.csv
          data/processed/batas_kabkota_jateng.geojson
Keluaran: outputs/simulasi_peta_pm25.png
          outputs/simulasi_moran_pm25.txt
Catatan : SEMUA ANGKA DI SINI ADALAH DATA SIMULASI, bukan pengukuran.
"""
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from esda.moran import Moran  # noqa: E402
from libpysal.weights import Queen, full2W  # noqa: E402

sys.path.insert(0, str(Path(__file__).parent))
from simulasi_kualitas_udara import bobot_queen_dari_geojson  # noqa: E402

BATAS = Path("data/processed/batas_kabkota_jateng.geojson")
PANEL = Path("data/processed/simulasi_pm25_jateng_panel.csv")
OUT_PETA = Path("outputs/simulasi_peta_pm25.png")
OUT_MORAN = Path("outputs/simulasi_moran_pm25.txt")
SEED = 2026


def main():
    OUT_PETA.parent.mkdir(parents=True, exist_ok=True)

    # gdf dan W dibangun dengan fungsi yang sama seperti saat simulasi, jadi urutannya cocok
    gdf, W = bobot_queen_dari_geojson(BATAS)
    panel = pd.read_csv(PANEL)

    rata = (
        panel.groupby("idx_wilayah")["pm25_simulasi_ugm3"]
        .mean()
        .reindex(range(len(gdf)))
    )
    if rata.isna().any():
        sys.exit("Ada wilayah tanpa data panel. Cek ulang urutan idx_wilayah.")
    gdf = gdf.assign(pm25_rata=rata.to_numpy())

    # Cek apakah Queen murni punya wilayah tanpa tetangga (jika ya, skrip simulasi memakai KNN)
    q = Queen.from_dataframe(gdf, use_index=False)
    pulau = list(q.islands)

    # Peta
    fig, ax = plt.subplots(figsize=(9, 7))
    gdf.plot(
        column="pm25_rata",
        cmap="YlOrRd",
        legend=True,
        ax=ax,
        edgecolor="grey",
        linewidth=0.4,
        legend_kwds={"label": "PM2.5 rata-rata (ug/m3), SIMULASI", "shrink": 0.7},
    )
    ax.set_title(
        "SIMULASI: rata-rata PM2.5 per kabupaten/kota Jawa Tengah\n"
        "(12 bulan, data simulasi, bukan pengukuran)",
        fontsize=12,
    )
    ax.set_axis_off()
    fig.savefig(OUT_PETA, dpi=200, bbox_inches="tight")
    plt.close(fig)

    # Moran's I global untuk rata-rata per wilayah
    np.random.seed(SEED)
    w = full2W(W)
    w.transform = "r"
    y = gdf["pm25_rata"].to_numpy()
    m = Moran(y, w, permutations=999)

    arah = "positif (mengelompok)" if m.I > m.EI else "negatif (menyebar)"
    teks = [
        "SIMULASI: Moran's I global, rata-rata PM2.5 per kab/kota Jawa Tengah",
        "Data simulasi, bukan pengukuran.",
        f"Bobot: Queen contiguity, row-standardized (n = {len(gdf)})",
        f"Wilayah tanpa tetangga pada Queen murni: {pulau if pulau else 'tidak ada'}",
        f"Seed permutasi: {SEED}, jumlah permutasi: 999",
        "",
        f"I        = {m.I:.6f}",
        f"E[I]     = {m.EI:.6f}",
        f"z-score  = {m.z_sim:.4f}",
        f"p (sim)  = {m.p_sim:.4f}  (dua sisi)",
        f"Arah     : {arah}",
    ]
    OUT_MORAN.write_text("\n".join(teks) + "\n", encoding="utf-8")

    print("\n".join(teks))
    print(f"Peta tersimpan: {OUT_PETA}")


if __name__ == "__main__":
    main()
