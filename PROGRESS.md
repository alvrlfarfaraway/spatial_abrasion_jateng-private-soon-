# Progres Analisis

Dokumen ini mencatat status tiap tahap, data yang tersedia, dan keterbatasannya.

## Rumusan 1: perubahan luas daratan pesisir Jawa Tengah (data citra nyata)

Status: selesai untuk pengambilan dan perhitungan luas. Interpretasi sebagai abrasi belum diverifikasi.

- Sumber citra: Landsat 8 Collection 2 Level 2 lewat Google Earth Engine. Landsat 9 tidak dipakai agar deret waktu konsisten.
- Jendela waktu: 1 Juni sampai 31 Oktober, komposit median per tahun, 2014 sampai 2025.
- Batas wilayah: FAO GAUL 2025, 35 kabupaten/kota di Jawa Tengah.
- Zona pesisir: buffer 2 km ke darat dan ke laut dari garis pantai.
- Hasil: `data/processed/luas_daratan_pesisir_jateng.csv` (420 baris, 35 wilayah dan 12 tahun) dan `data/processed/luas_zona_pesisir_per_kab.csv`.

Keterbatasan:
- Luas daratan dalam zona adalah proksi, bukan pengukuran abrasi langsung. Perubahan juga bisa berasal dari tambak, sedimentasi muara, atau klasifikasi NDWI.
- Pekalongan menunjukkan penurunan dari sekitar 1.854 ha (2014) ke 1.028 ha (2025). Lonjakan NDWI rata-rata antara 2020 dan 2021 belum dijelaskan.
- Garis pantai Wonogiri (Paranggupito) berasal dari sumber non-resmi dan belum diverifikasi.

## Rumusan 2: kualitas udara PM2.5 (simulasi)

Status: skrip simulasi selesai dan menghasilkan panel 35 wilayah x 12 bulan. Kalibrasi terhadap data ISPU riil belum dilakukan.

- Model: `y = (I - rho W)^(-1) (X beta + musim + e)` dengan matriks bobot Queen dan rho = 0,6.
- Seed: 2026. Hasil dapat direproduksi dengan kode di `scripts/simulasi_kualitas_udara.py`.
- Hasil: `data/processed/simulasi_pm25_jateng_panel.csv`. Semua nilai bersifat simulasi dan diberi label SIMULASI.
- Parameter kalibrasi (rata-rata 25 ug/m3, SD 6) masih placeholder.

## Yang belum dikerjakan

- Pengambilan data ISPU atau PM2.5 riil untuk Jawa Tengah dan kalibrasi rumusan 2.
- Variabel penjelas riil (kepadatan kendaraan, industri, ruang hijau) dari BPS.
- Analisis LISA dan Getis-Ord Gi* pada data rumusan 2.
- Verifikasi lisensi GADM sebelum batas wilayah dipublikasikan ulang.
- Verifikasi sumber pustaka pendukung.
