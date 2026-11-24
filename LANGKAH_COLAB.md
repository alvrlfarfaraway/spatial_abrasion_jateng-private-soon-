# Langkah Menjalankan di Google Colab

Panduan ini untuk menyiapkan data dan batas wilayah tanpa terminal.

## 1. Ambil repo dan instal paket

Buka Google Colab, buat notebook baru, lalu jalankan sel berikut satu per satu:

    !git clone https://github.com/alvrlfarfaraway/spatial_abrasion_jateng-private-soon-.git
    %cd spatial_abrasion_jateng-private-soon-
    !pip install -q libpysal esda pyyaml requests
    !mkdir -p data/raw data/processed outputs
    !python scripts/ambil_batas_wilayah.py

## 2. Cek jumlah wilayah

    import geopandas as gpd
    gdf = gpd.read_file("data/processed/batas_kabkota_jateng.geojson")
    print(len(gdf))

Hasilnya harus 35. Kalau tidak, berhenti dan laporkan ke ketua kelompok.

## 3. Cek data hasil olahan

Tiga CSV sudah ada di data/processed/:
- luas_daratan_pesisir_jateng.csv (rumusan 1, data riil)
- luas_zona_pesisir_per_kab.csv (rumusan 1, data riil)
- simulasi_pm25_jateng_panel.csv (rumusan 2, SIMULASI)

Jangan mengubah isi CSV. Semua angka dari rumusan 2 wajib diberi label SIMULASI.

## 4. Simpan hasil

Sesi Colab hilang saat ditutup. Simpan hasil ke Google Drive atau unduh sebelum menutup sesi.

## 5. Analisis

Bagian analisis (Moran's I, LISA, dan Gi*) belum dibuat. Akan ditambahkan setelah metode disepakati kelompok.
