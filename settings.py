"""
settings.py
Pusat konfigurasi environment variables untuk aplikasi Rafsistant.
Semua data rahasia (Token, ID, Password) wajib dimasukkan ke dalam file .env, 
bukan ditulis langsung (hardcoded) di dalam kode program.
"""

import os
from dotenv import load_dotenv

# Memuat environment variables dari file .env
load_dotenv()

# ==========================================
# KONFIGURASI UTAMA BOT & USER
# ==========================================
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
CHAT_ID_BAGINDA = os.getenv("CHAT_ID_BAGINDA", "")

# ==========================================
# KONFIGURASI INTEGRASI PIHAK KETIGA
# ==========================================
ID_SPREADSHEET = os.getenv("ID_SPREADSHEET", "")
NIM_KAMPUS = os.getenv("NIM_KAMPUS", "")
PASSWORD_KAMPUS = os.getenv("PASSWORD_KAMPUS", "")

# Validasi Keamanan: Pastikan variabel esensial tidak kosong
if not BOT_TOKEN:
    raise ValueError("[SYSTEM ERROR] BOT_TOKEN tidak ditemukan! Pastikan Anda telah mengatur file .env.")
if not CHAT_ID_BAGINDA:
    print("[WARNING] CHAT_ID_BAGINDA kosong. Bot mungkin tidak bisa mengirim laporan otomatis.")