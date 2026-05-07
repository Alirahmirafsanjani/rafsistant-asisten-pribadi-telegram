"""
webhook_gopay.py
Server mikro berbasis Flask untuk mendengarkan webhook (notifikasi aplikasi eksternal seperti GoPay).
Teks notifikasi yang relevan akan di-parsing dan dicatat secara otomatis ke Google Sheets.
"""

from flask import Flask, request
import requests
from datetime import datetime
import re

from google_api import catat_ke_sheets
from settings import BOT_TOKEN, CHAT_ID_BAGINDA, ID_SPREADSHEET

app = Flask(__name__)

def kirim_telegram(pesan):
    """Mengirim pesan notifikasi push secara langsung ke pengguna via Telegram API."""
    if not BOT_TOKEN or not CHAT_ID_BAGINDA:
        print("[WARNING] Konfigurasi Telegram tidak lengkap, notifikasi dilewati.")
        return 500
        
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    try:
        r = requests.post(url, json={"chat_id": CHAT_ID_BAGINDA, "text": pesan, "parse_mode": "Markdown"})
        return r.status_code
    except Exception as e:
        print(f"⚠️ Gagal mengirim pesan ke Telegram: {e}")
        return 500

@app.route('/gopay', methods=['POST'])
def terima_notif():
    """Endpoint utama untuk memproses payload notifikasi masuk."""
    data = request.json
    if not data or 'teks' not in data: 
        return "Bad Request: Data tidak valid", 400
        
    teks_notif = data['teks']
    teks_kecil = teks_notif.lower()
    tanggal = datetime.now().strftime("%d/%m/%Y %H:%M")

    # Filter sederhana untuk mengabaikan notifikasi promosi
    kata_spam = ["koin", "klik disini", "promo", "cashback", "dapatkan", "s.d.", "s.d", "voucher", "diskon"]
    if any(spam in teks_kecil for spam in kata_spam):
        return "Ignored: Promosi", 200

    # Mengekstrak pola nominal mata uang Rupiah
    pola_nominal = r'rp\s*([\d\.]+)|(\d{1,3}(?:\.\d{3})+)'
    kecocokan = re.search(pola_nominal, teks_kecil)
    
    if not kecocokan:
        return "Ignored: Bukan transaksi finansial", 200
        
    angka_kotor = kecocokan.group(1) if kecocokan.group(1) else kecocokan.group(2)
    angka_kotor = angka_kotor.rstrip('.') 
    jumlah_bersih = angka_kotor.replace('.', '')

    # Mengklasifikasikan jenis transaksi (Masuk / Keluar)
    kata_kunci_masuk = ["masuk", "diterima", "top up", "topup", "isi saldo", "penerimaan", "bertambah", "terima transfer", "menerima"]
    jenis = "MASUK" if any(k in teks_kecil for k in kata_kunci_masuk) else "KELUAR"
    emoji = "💰" if jenis == "MASUK" else "💸"

    # Proses pencatatan ke cloud database (Google Sheets)
    try:
        berhasil = catat_ke_sheets(ID_SPREADSHEET, tanggal, jenis, "Auto-Catat Sistem", jumlah_bersih, teks_notif)
        if berhasil:
            kirim_telegram(f"{emoji} *AUTO-CATAT {jenis} BERHASIL!*\n━━━━━━━━━━━━━━━\n*Jumlah:* Rp {jumlah_bersih}\n*Detail:* {teks_notif}")
    except Exception as e:
        print(f"[SERVER ERROR] Pencatatan gagal: {e}")
        kirim_telegram(f"⚠️ *Peringatan Sistem!* Gagal melakukan auto-catat transaksi.")

    return "OK", 200

if __name__ == '__main__':
    # Jalankan server lokal di port 5000
    app.run(host='0.0.0.0', port=5000)