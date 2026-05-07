from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

def get_google_creds():
    # Mengambil tiket akses yang sudah Baginda buat
    return Credentials.from_authorized_user_file('token.json')

def tambah_tugas_ke_google(nama_tugas):
    try:
        creds = get_google_creds()
        service = build('tasks', 'v1', credentials=creds)
        task = {'title': nama_tugas}
        service.tasks().insert(tasklist='@default', body=task).execute()
        return True
    except:
        return False

def tambah_agenda_ke_google(jadwal, kegiatan):
    try:
        creds = get_google_creds()
        service = build('calendar', 'v3', credentials=creds)
        kalimat_ajaib = f"{kegiatan} on {jadwal}"
        hasil = service.events().quickAdd(calendarId='primary', text=kalimat_ajaib).execute()
        return hasil.get('htmlLink')
    except:
        return None

def catat_ke_sheets(spreadsheet_id, tanggal, tipe, kategori, jumlah, keterangan):
    try:
        creds = get_google_creds()
        service = build('sheets', 'v4', credentials=creds)
        # Menyiapkan baris untuk harta Baginda
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
        # Hamba akan lapor di terminal jika ada masalah dengan Sheets
        print(f"DEBUG ERROR SHEETS: {e}")
        return False

def baca_dari_sheets(spreadsheet_id):
    try:
        creds = get_google_creds()
        service = build('sheets', 'v4', credentials=creds)
        # Membaca dari kolom A sampai E di Sheet1
        result = service.spreadsheets().values().get(
            spreadsheetId=spreadsheet_id,
            range="Sheet1!A:E"
        ).execute()
        return result.get('values', [])
    except Exception as e:
        print(f"DEBUG BACA SHEETS: {e}")
        return None


