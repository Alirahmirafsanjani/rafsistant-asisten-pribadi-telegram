import sqlite3

DB_NAME = 'catatan_tugas.db'

def init_tugas_db():
    """Membuat tabel jika belum ada saat bot pertama kali menyala."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS tugas
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  nama_tugas TEXT)''')
    conn.commit()
    conn.close()

def tambah_tugas(nama_tugas):
    """Memasukkan tugas baru ke database."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("INSERT INTO tugas (nama_tugas) VALUES (?)", (nama_tugas,))
    conn.commit()
    conn.close()

def ambil_semua_tugas():
    """Menarik semua data tugas dari database."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT id, nama_tugas FROM tugas")
    data = c.fetchall()
    conn.close()
    return data

def hapus_tugas(id_tugas):
    """Menghapus tugas berdasarkan nomor ID."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("DELETE FROM tugas WHERE id=?", (id_tugas,))
    conn.commit()
    conn.close()
