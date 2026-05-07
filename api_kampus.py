"""
api_kampus.py
Modul untuk menangani integrasi dengan portal akademik kampus (Alma Ata).
Digunakan untuk melakukan otentikasi dan menarik data jadwal (Reguler & UTS).
"""

import requests
import hashlib
from bs4 import BeautifulSoup
import json

def tarik_jadwal_uts(nim, password):
    """
    Fungsi untuk menarik jadwal kuliah dan UTS dari portal kampus.
    Membutuhkan kredensial pengguna (NIM dan Password).
    """
    session = requests.Session()
    home_url = "https://raising.almaata.ac.id/welcome"
    login_url = "https://raising.almaata.ac.id/auth/login"

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
        'X-Requested-With': 'XMLHttpRequest'
    }

    try:
        # 1. Proses Autentikasi (Login)
        resp_home = session.get(home_url, headers=headers, timeout=10)
        csrf_token = BeautifulSoup(resp_home.text, 'html.parser').find('input', {'name': 'csrf_test_name'})['value']

        payload = {
            'csrf_test_name': csrf_token,
            'f1': hashlib.md5(nim.encode()).hexdigest(),
            'f2': hashlib.md5(password.encode()).hexdigest(),
            'slogin': 'LOGIN'
        }
        dash_resp = session.post(login_url, data=payload, headers=headers, timeout=15)

        if "dashboard" not in dash_resp.url:
            return "⚠️ Akses ditolak. Gagal login, periksa kembali NIM dan Password di konfigurasi."

        unique_id = dash_resp.url.split('/')[3]
        pesan_final = ""

        # ==========================================
        # A. PENARIKAN JADWAL KULIAH REGULER
        # ==========================================
        try:
            api_kuliah = f"https://raising.almaata.ac.id/{unique_id}/api/perkuliahan/get_jadwal_kuliah_mahasiswa/{nim}"
            resp_k = session.get(api_kuliah, headers=headers, timeout=10)
            data_k = resp_k.json()
            
            pesan_final += "📘 *JADWAL KULIAH AKTIF* 📘\n"
            
            if "data" in data_k and data_k["data"]:
                jadwal_harian = {}
                for item in data_k["data"]:
                    def bersihkan(teks):
                        return BeautifulSoup(str(teks), "html.parser").text.strip()
                    
                    if isinstance(item, list) and len(item) > 3:
                        matkul = bersihkan(item[1])
                        waktu_ruang = bersihkan(item[3])
                        tgl = "Jadwal Reguler" 
                        if tgl not in jadwal_harian: jadwal_harian[tgl] = []
                        jadwal_harian[tgl].append(f" 🔹 {waktu_ruang} | {matkul}")
                    
                    elif isinstance(item, dict):
                        tgl = bersihkan(item.get('tanggal', item.get('hari', 'Reguler')))
                        matkul = bersihkan(item.get('nama_matakuliah', item.get('matakuliah', 'Matkul')))
                        waktu = bersihkan(item.get('waktu', item.get('jam', '')))
                        ruang = bersihkan(item.get('ruang', ''))
                        
                        detail = f"{waktu} | {matkul}"
                        if ruang: detail += f" ({ruang})"
                        
                        if tgl not in jadwal_harian: jadwal_harian[tgl] = []
                        jadwal_harian[tgl].append(f" 🔹 {detail}")

                for tgl, lists in jadwal_harian.items():
                    pesan_final += f"\n🗓️ *{tgl}*\n" + "\n".join(lists) + "\n"
            else:
                pesan_final += "\n⚠️ Tidak ada jadwal kuliah aktif yang ditemukan saat ini.\n"
        except Exception as e:
            pesan_final += f"\n⚠️ [ERROR] Gagal memuat jadwal reguler: {e}\n"

        pesan_final += "\n"

        # ==========================================
        # B. PENARIKAN JADWAL UTS
        # ==========================================
        try:
            api_uts = f"https://raising.almaata.ac.id/{unique_id}/api/perkuliahan/get_jadwal_ujian_mahasiswa/{nim}"
            api_resp = session.get(api_uts, headers=headers, timeout=10)
            data_json = api_resp.json()

            pesan_final += "🎓 *JADWAL UJIAN (UTS)* 🎓\n"

            if data_json.get("status") == "success" and data_json.get("data"):
                jadwal_per_hari = {}
                for ujian in data_json["data"]:
                    tgl = ujian['tanggal_ujian']
                    if tgl not in jadwal_per_hari:
                        jadwal_per_hari[tgl] = []
                    jadwal_per_hari[tgl].append(ujian)
                
                for tgl, daftar_matkul in jadwal_per_hari.items():
                    pesan_final += f"\n🗓️ *{tgl}*\n"
                    for ujian in daftar_matkul:
                        matkul = ujian['nama_matakuliah'].replace('\n', ' ')
                        waktu = ujian['waktu_ujian']
                        ruang = ujian['nama_ruang']
                        jenis = ujian['jenis_ujian']
                        pesan_final += f" 🔹 {waktu} | {matkul} ({ruang}) - {jenis}\n"
            else:
                pesan_final += "\n⚠️ Jadwal UTS belum tersedia di sistem.\n"
        except Exception as e:
            pass 

        pesan_final += "\n_Data ditarik secara otomatis dari sistem akademik._ 🚀"
        return pesan_final

    except Exception as e:
        return f"⚠️ [SYSTEM ERROR] Gangguan jaringan saat mengakses sistem: {e}"