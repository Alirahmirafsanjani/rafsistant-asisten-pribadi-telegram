import requests
import hashlib
from bs4 import BeautifulSoup
import json

def tarik_jadwal_uts(nim, password):
    session = requests.Session()
    home_url = "https://raising.almaata.ac.id/welcome"
    login_url = "https://raising.almaata.ac.id/auth/login"

    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36',
        'X-Requested-With': 'XMLHttpRequest'
    }

    try:
        # 1. Login
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
            return "⚠️ Gagal login. Cek kembali NIM dan Password Baginda."

        unique_id = dash_resp.url.split('/')[3]
        pesan_final = ""

        # ==========================================
        # A. TARIK JADWAL KULIAH REGULER (JALUR API)
        # ==========================================
        try:
            api_kuliah = f"https://raising.almaata.ac.id/{unique_id}/api/perkuliahan/get_jadwal_kuliah_mahasiswa/{nim}"
            resp_k = session.get(api_kuliah, headers=headers, timeout=10)
            data_k = resp_k.json()
            
            pesan_final += "📘 *JADWAL KULIAH BAGINDA ALI* 📘\n"
            
            if "data" in data_k and data_k["data"]:
                jadwal_harian = {}
                for item in data_k["data"]:
                    # Pembersih tag HTML liar dari DataTables
                    def bersihkan(teks):
                        return BeautifulSoup(str(teks), "html.parser").text.strip()
                    
                    # Logika Pemecah Array (Jika API membalas dengan format List)
                    if isinstance(item, list) and len(item) > 3:
                        matkul = bersihkan(item[1])
                        waktu_ruang = bersihkan(item[3])
                        
                        tgl = "Jadwal Reguler" 
                        if tgl not in jadwal_harian: jadwal_harian[tgl] = []
                        jadwal_harian[tgl].append(f" 🔹 {waktu_ruang} | {matkul}")
                    
                    # Logika Pemecah Kamus (Jika API membalas dengan format Dictionary)
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
                pesan_final += "\n⚠️ Tidak ada jadwal kuliah aktif yang ditemukan.\n"
        except Exception as e:
            pesan_final += f"\n⚠️ Gagal menembus API Kuliah: {e}\n"

        pesan_final += "\n"

        # ==========================================
        # B. TARIK JADWAL UTS (JALUR API)
        # ==========================================
        try:
            api_uts = f"https://raising.almaata.ac.id/{unique_id}/api/perkuliahan/get_jadwal_ujian_mahasiswa/{nim}"
            api_resp = session.get(api_uts, headers=headers, timeout=10)
            data_json = api_resp.json()

            pesan_final += "🎓 *JADWAL UTS BAGINDA ALI* 🎓\n"

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
                pesan_final += "\n⚠️ Jadwal UTS kosong atau belum dirilis.\n"
        except Exception as e:
            pass 

        pesan_final += "\n*Tetap produktif dan semangat memimpin HIMSI, Ketua!* 🚀👑"
        return pesan_final

    except Exception as e:
        return f"⚠️ Terjadi kesalahan jaringan sistem: {e}"
