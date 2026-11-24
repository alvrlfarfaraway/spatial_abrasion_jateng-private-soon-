# Abrasi dan Kualitas Udara Jawa Tengah: Kode Analisis Spasial

Kode untuk tugas Analisis Data Spasial untuk Data Lingkungan (Prodi Statistika dan Sains Data, UNNES).
Repo ini berisi kode, konfigurasi, dan hasil olahan dalam bentuk CSV. Data mentah dan GeoJSON tidak disertakan dan dibuat ulang oleh skrip.

## Isi

- `scripts/ambil_batas_wilayah.py`: unduh batas kabupaten/kota dari GADM 4.1 dan simpan versi Jawa Tengah.
- `scripts/garis_pantai_lokal.py`: buat garis pantai lokal dari mask daratan GADM.
- `scripts/gee_luas_daratan_pesisir.py`: hitung luas daratan di zona pesisir per tahun dari Landsat 8 (NDWI) lewat Google Earth Engine.
- `scripts/simulasi_kualitas_udara.py`: simulasi panel PM2.5 dengan ketergantungan spasial (matriks bobot Queen).
- `scripts/simulasi_peta_dan_moran.py`: peta simulasi dan statistik Moran's I.
- Skrip analisis statistik spasial rumusan 1: persentase perubahan luas per kabupaten/kota, Moran's I, dan Getis-Ord Gi* (belum dibuat).
- Skrip LISA dan Getis-Ord Gi* untuk rumusan 2 (belum dibuat).
- `scripts/scrape_tabel.py`: ambil tabel dari halaman web, dengan cek robots.txt dan jeda 2 detik.
- `config/sumber_data.yaml`: daftar sumber data dan parameter.
- `PROGRESS.md`: status tiap rumusan, data yang tersedia, dan keterbatasannya.
- `data/processed/`: tiga CSV hasil olahan.

## Cara menjalankan

```bash
pip install -r requirements.txt
python scripts/ambil_batas_wilayah.py
python scripts/garis_pantai_lokal.py
python scripts/gee_luas_daratan_pesisir.py --project ID_PROYEK_GEE
python scripts/simulasi_kualitas_udara.py
python scripts/simulasi_peta_dan_moran.py
```

Skrip Google Earth Engine memerlukan akun dan proyek GEE yang sudah terdaftar, serta autentikasi dengan `earthengine authenticate`.

Skrip analisis statistik spasial akan ditambahkan setelah metode disepakati.

## Catatan

- Batas wilayah berasal dari GADM. Lisensinya hanya untuk penggunaan akademik dan non-komersial. Periksa `gadm.org/license` sebelum memakai ulang data.
- Hasil pada bagian pesisir adalah proksi perubahan luas daratan dalam zona, bukan pengukuran abrasi langsung.
- Data simulasi tidak mewakili pengukuran nyata.
