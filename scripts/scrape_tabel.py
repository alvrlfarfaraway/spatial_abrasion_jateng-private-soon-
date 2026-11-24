"""Scraper sopan untuk tabel HTML publik. Sumber dibaca dari config/sumber_data.yaml (bagian tabel_web).

Jalankan:
    python scripts/scrape_tabel.py --semua
    python scripts/scrape_tabel.py --id ispu_databoks_contoh
Hasil: data/raw/<id>.html dan data/raw/<id>_tabel_<n>.csv, catatan akses ditambah ke data/sumber_data.md

Aturan: cek robots.txt, jeda 2 detik, user agent jelas, cache. Tidak login, tidak lewati captcha.
"""
import argparse
import datetime as dt
import io
import time
import urllib.robotparser
from pathlib import Path
from urllib.parse import urlparse

import pandas as pd
import requests
import yaml

UA = "tugas-kuliah-unnes/1.0 (data pendidikan; kontak: isi_email_sendiri)"
RAW = Path("data/raw")
JEDA_DETIK = 2.0


def boleh_diambil(url):
    u = urlparse(url)
    rp = urllib.robotparser.RobotFileParser()
    rp.set_url(f"{u.scheme}://{u.netloc}/robots.txt")
    try:
        rp.read()
    except Exception:
        return True  # robots.txt tidak terbaca: lanjut, tapi tetap sopan
    return rp.can_fetch(UA, url)


def ambil(item):
    sid, url = item["id"], item["url"]
    if not boleh_diambil(url):
        print(f"[lewati] {sid}: dilarang robots.txt")
        return
    html_path = RAW / f"{sid}.html"
    if html_path.exists():
        html = html_path.read_text(encoding="utf-8")
        print(f"[cache] {sid}")
    else:
        r = requests.get(url, headers={"User-Agent": UA}, timeout=60)
        if r.status_code != 200:
            print(f"[gagal] {sid}: HTTP {r.status_code}")
            return
        html = r.text
        html_path.write_text(html, encoding="utf-8")
        time.sleep(JEDA_DETIK)
    try:
        tabel = pd.read_html(io.StringIO(html))
    except ValueError:
        print(f"[kosong] {sid}: tidak ada <table>. Mungkin dimuat JavaScript, cari API-nya di tab Network.")
        return
    for i, t in enumerate(tabel):
        t.to_csv(RAW / f"{sid}_tabel_{i}.csv", index=False)
    print(f"[ok] {sid}: {len(tabel)} tabel")
    with open("data/sumber_data.md", "a", encoding="utf-8") as fh:
        fh.write(f"- {sid} | {url} | diakses {dt.date.today()} | {item.get('keterangan', '')}\n")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--semua", action="store_true")
    p.add_argument("--id")
    a = p.parse_args()
    RAW.mkdir(parents=True, exist_ok=True)
    cfg = yaml.safe_load(open("config/sumber_data.yaml", encoding="utf-8"))
    daftar = cfg["tabel_web"]
    if a.id:
        daftar = [d for d in daftar if d["id"] == a.id]
    elif not a.semua:
        p.error("pakai --semua atau --id")
    for item in daftar:
        ambil(item)


if __name__ == "__main__":
    main()
