from flask import Flask, request
import requests
from datetime import datetime
import re

from google_api import catat_ke_sheets
from settings import BOT_TOKEN, CHAT_ID_BAGINDA

app = Flask(__name__)

# ID Brankas Sheets Baginda
ID_SPREADSHEET = "ID_SPREADSHEET_KAMU"  # Ganti dengan ID spreadsheet yang benar

def kirim_telegram(pesan):
    """Fungsi untuk mengirim laporan ke Telegram Baginda"""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    try:
        r = requests.post(url, json={"chat_id": CHAT_ID_BAGINDA, "text": pesan, "parse_mode": "Markdown"})
        return r.status_code
    except Exception as e:
        print(f"⚠️ Gagal mengirim pesan ke Telegram: {e}")
        return 500

@app.route('/gopay', methods=['POST'])
def terima_notif():
    data = request.json
    if not data or 'teks' not in data: return "Gagal", 400
        
    teks_notif = data['teks']
    teks_kecil = teks_notif.lower()
    tanggal = datetime.now().strftime("%d/%m/%Y %H:%M")

    kata_spam = ["koin", "klik disini", "promo", "cashback", "dapatkan", "s.d.", "s.d", "voucher", "diskon"]
    if any(spam in teks_kecil for spam in kata_spam):
        return "Abaikan promo", 200

    pola_nominal = r'rp\s*([\d\.]+)|(\d{1,3}(?:\.\d{3})+)'
    kecocokan = re.search(pola_nominal, teks_kecil)
    
    if not kecocokan:
        return "Bukan transaksi", 200
        
    angka_kotor = kecocokan.group(1) if kecocokan.group(1) else kecocokan.group(2)
    angka_kotor = angka_kotor.rstrip('.') 
    jumlah_bersih = angka_kotor.replace('.', '')

    kata_kunci_masuk = ["masuk", "diterima", "top up", "topup", "isi saldo", "penerimaan", "bertambah", "terima transfer", "menerima"]
    jenis = "MASUK" if any(k in teks_kecil for k in kata_kunci_masuk) else "KELUAR"
    emoji = "💰" if jenis == "MASUK" else "💸"

    try:
        berhasil = catat_ke_sheets(ID_SPREADSHEET, tanggal, jenis, "Auto-Catat", jumlah_bersih, teks_notif)
        if berhasil:
            kirim_telegram(f"{emoji} *AUTO-CATAT {jenis} BERHASIL!*\n━━━━━━━━━━━━━━━\n*Jumlah:* Rp {jumlah_bersih}\n*Detail:* {teks_notif}")
    except Exception as e:
        print(f"Error: {e}")
        kirim_telegram(f"⚠️ *Gagal mencatat!* Terjadi kesalahan server.")

    return "OK", 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)