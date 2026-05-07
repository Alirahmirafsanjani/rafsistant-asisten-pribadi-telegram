"""
google_api.py
Modul untuk berinteraksi dengan Google Workspace APIs.
Mencakup fungsi untuk manipulasi Google Tasks, Google Calendar, dan Google Sheets.
Membutuhkan file token.json yang di-generate dari proses OAuth2.
"""

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

def get_google_creds():
    """Mengambil dan memvalidasi token akses otentikasi Google."""
    try:
        return Credentials.from_authorized_user_file('token.json')
    except Exception as e:
        print(f"[ERROR] Kredensial Google gagal dimuat: {e}")
        return None

def tambah_tugas_ke_google(nama_tugas):
    """Menambahkan item tugas baru ke daftar Google Tasks default."""
    try:
        creds = get_google_creds()
        if not creds: return False
        
        service = build('tasks', 'v1', credentials=creds)
        task = {'title': nama_tugas}
        service.tasks().insert(tasklist='@default', body=task).execute()
        return True
    except Exception as e:
        print(f"[ERROR] Google Tasks API: {e}")
        return False

def tambah_agenda_ke_google(jadwal, kegiatan):
    """Menjadwalkan acara (event) baru ke Google Calendar utama pengguna."""
    try:
        creds = get_google_creds()
        if not creds: return None
        
        service = build('calendar', 'v3', credentials=creds)
        kalimat_ajaib = f"{kegiatan} on {jadwal}"
        hasil = service.events().quickAdd(calendarId='primary', text=kalimat_ajaib).execute()
        return hasil.get('htmlLink')
    except Exception as e:
        print(f"[ERROR] Google Calendar API: {e}")
        return None

def catat_ke_sheets(spreadsheet_id, tanggal, tipe, kategori, jumlah, keterangan):
    """Mencatat entri keuangan baru ke dalam dokumen Google Sheets."""
    try:
        creds = get_google_creds()
        if not creds: return False
        
        service = build('sheets', 'v4', credentials=creds)
        baris = [[tanggal, tipe, kategori, jumlah, keterangan]]
        body = {'values': baris}
        
        service.spreadsheets().values().append(
            spreadsheetId=spreadsheet_id,
            range="Sheet1!A1",
            valueInputOption="USER_ENTERED",
            body=body
        ).execute()
        return True
    except Exception as e:
        print(f"[ERROR] Google Sheets API (Write): {e}")
        return False

def baca_dari_sheets(spreadsheet_id):
    """Membaca riwayat pencatatan dari kolom A hingga E di Google Sheets."""
    try:
        creds = get_google_creds()
        if not creds: return None
        
        service = build('sheets', 'v4', credentials=creds)
        result = service.spreadsheets().values().get(
            spreadsheetId=spreadsheet_id,
            range="Sheet1!A:E"
        ).execute()
        return result.get('values', [])
    except Exception as e:
        print(f"[ERROR] Google Sheets API (Read): {e}")
        return None