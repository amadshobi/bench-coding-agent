# Contributing to CIVIL Benchmark Engine

Terima kasih sudah tertarik berkontribusi! 🎉 Proyek ini hidup dari kontribusi komunitas. Panduan ini akan membantu kamu mulai berkontribusi dengan lancar.

## 📋 Cara Berkontribusi (Alur Singkat)

1. **Fork** — Fork repositori ini ke akun GitHub kamu.
2. **Clone** — Clone fork kamu ke lokal:
   ```bash
   git clone https://github.com/<username>/benchmark-engine.git
   cd benchmark-engine
   ```
3. **Develop** — Buat branch baru untuk perubahanmu:
   ```bash
   git checkout -b feat/my-improvement
   ```
4. **Test** — Pastikan perubahanmu lolos uji (lihat di bawah).
5. **Submit PR** — Push branch dan buka Pull Request ke branch `main` dengan template PR yang disediakan.

## 🛠️ Setup Environment Development

Proyek ini **stdlib-only** (tidak ada dependency eksternal). Yang kamu butuhkan:

- **Python 3.14.4+**
- **OpenRouter API key** (untuk menjalankan benchmark sungguhan)

Langkah setup:

```bash
# Buat & aktifkan virtual environment (WAJIB)
python3 -m venv .venv
source .venv/bin/activate        # Linux/macOS
# .venv\Scripts\activate         # Windows

# Copy file environment contoh
cp .env.example .env
# Isi OPENROUTER_API_KEY di .env (jangan commit file .env!)
```

Menjalankan benchmark secara lokal untuk verifikasi:

```bash
python3 scripts/blin run
```

## 📐 Coding Standards

- Ikuti **gaya penulisan kode yang sudah ada** di repositori ini (penamaan, struktur modul, docstring).
- Tetap di dalam batas layer yang benar:
  - **Router** = routing, **Service** = business logic, **Storage** = penyimpanan data.
  - Jangan suntik logic ke layer yang salah.
- Hindari dependency eksternal baru kecuali benar-benar diperlukan.
- Tulis **unit test** untuk logic baru, dan update dokumentasi/README bila perilaku berubah.
- Gunakan bahasa Indonesia untuk komentar/diskusi, istilah teknis tetap dalam English.

## 🐛 Melaporkan Bug & Usulan Fitur

Gunakan **issue template** yang sudah disediakan — jangan buat issue kosong:

- **Bug report** → jelaskan langkah reproduksi, expected vs actual behavior, dan environment (OS, versi Python, commit).
- **Feature request** → jelaskan fitur, usulan implementasi, dan alasan kenapa fitur ini dibutuhkan.

Template ini membantu maintainer merespons lebih cepat dan akurat.

## ✅ Sebelum Membuka PR

Pastikan checklist di template PR tercentang:

- [ ] Code follows existing style guidelines
- [ ] Added unit tests
- [ ] Updated documentation/README
- [ ] Verified changes in a local benchmark run

## 💬 Butuh Bantuan?

Jangan ragu untuk membuka issue dengan pertanyaan, atau diskusikan ide sebelum mengerjakan perubahan besar. Kontribusi kecil maupun besar sangat dihargai.

Selamat berkontribusi! 🚀
