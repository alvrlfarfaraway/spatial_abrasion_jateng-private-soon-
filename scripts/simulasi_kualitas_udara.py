"""Simulasi data panel kualitas udara (PM2.5) dengan ketergantungan spasial, kab/kota Jawa Tengah.

Model, untuk bulan t:
    y_t = (I - rho W)^(-1) (b0 + X b + musim_t + e_t),   e_t ~ N(0, sigma^2 I)
W = bobot Queen (row-standardized). X = kepadatan kendaraan, intensitas industri, ruang hijau
(juga dibuat berkorelasi spasial). Hasil diskalakan ke rata-rata dan sebaran dari config kalibrasi.

Jalankan: python scripts/simulasi_kualitas_udara.py --seed 2026
Hasil   : data/processed/simulasi_pm25_jateng_panel.csv  (SEMUA ANGKA SIMULASI, bukan pengukuran)
"""
import argparse
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

OUT = Path("data/processed/simulasi_pm25_jateng_panel.csv")


def invers_spasial(W, rho):
    n = W.shape[0]
    return np.linalg.inv(np.eye(n) - rho * W)


def simulasi_panel(W, rho=0.6, beta=(0.8, 0.6, -0.5), sigma=0.5, n_bulan=12,
                   amplitudo_musim=0.6, bulan_puncak=8, mu=25.0, sd=6.0, seed=2026):
    """Kembalikan (DataFrame panel tanpa nama wilayah, matriks X). W harus row-standardized."""
    rng = np.random.default_rng(seed)
    n = W.shape[0]
    A = invers_spasial(W, rho)

    # kovariat berkorelasi spasial, dibakukan
    X = np.column_stack([invers_spasial(W, 0.5) @ rng.normal(size=n) for _ in range(len(beta))])
    X = (X - X.mean(0)) / X.std(0)

    baris = []
    mentah = np.zeros((n, n_bulan))
    for t in range(n_bulan):
        musim = amplitudo_musim * np.cos(2 * np.pi * ((t + 1) - bulan_puncak) / 12)
        eps = rng.normal(0, sigma, size=n)
        mentah[:, t] = A @ (X @ np.array(beta) + musim + eps)

    z = (mentah - mentah.mean()) / mentah.std()
    pm25 = np.clip(mu + sd * z, 1.0, None)

    for i in range(n):
        for t in range(n_bulan):
            baris.append(
                {
                    "idx_wilayah": i,
                    "bulan": t + 1,
                    "pm25_simulasi_ugm3": round(float(pm25[i, t]), 2),
                    "kepadatan_kendaraan_simulasi_z": round(float(X[i, 0]), 3),
                    "intensitas_industri_simulasi_z": round(float(X[i, 1]), 3),
                    "ruang_hijau_simulasi_z": round(float(X[i, 2]), 3),
                }
            )
    return pd.DataFrame(baris), X


def bobot_queen_dari_geojson(path):
    import geopandas as gpd
    from libpysal.weights import Queen

    gdf = gpd.read_file(path)
    # GADM juga memuat badan air (mis. Waduk Kedungombo). Unit analisis hanya kab/kota.
    gdf = gdf[gdf["tipe"] != "WaterBody"].reset_index(drop=True)
    w = Queen.from_dataframe(gdf, use_index=False)
    if w.islands:
        # pulau/kota terpencil: sambungkan ke 3 tetangga terdekat agar W tidak punya baris kosong
        from libpysal.weights import KNN
        w = KNN.from_dataframe(gdf, k=3)
    w.transform = "r"
    W = np.zeros((w.n, w.n))
    for i, nb in w.neighbors.items():
        for j, wij in zip(nb, w.weights[i]):
            W[i, j] = wij
    return gdf, W


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--batas", default="data/processed/batas_kabkota_jateng.geojson")
    p.add_argument("--rho", type=float, default=0.6)
    p.add_argument("--seed", type=int, default=2026)
    a = p.parse_args()

    kal = yaml.safe_load(open("config/sumber_data.yaml", encoding="utf-8"))["kalibrasi_simulasi"]
    gdf, W = bobot_queen_dari_geojson(a.batas)
    df, _ = simulasi_panel(W, rho=a.rho, mu=kal["pm25_rata_rata_ugm3"],
                           sd=kal["pm25_sd_antar_wilayah"], seed=a.seed)
    df["nama_wilayah"] = df["idx_wilayah"].map(gdf["nama_wilayah"])
    OUT.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT, index=False)
    print(f"Tersimpan: {OUT} ({len(df)} baris). INGAT: data simulasi, beri label di makalah.")


if __name__ == "__main__":
    main()
