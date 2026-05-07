import sqlite3

DB_NAME = 'catatan_agenda.db'

def init_agenda_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS agenda
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  jadwal TEXT,
                  kegiatan TEXT)''')
    conn.commit()
    conn.close()

def tambah_agenda(jadwal, kegiatan):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("INSERT INTO agenda (jadwal, kegiatan) VALUES (?, ?)", (jadwal, kegiatan))
    conn.commit()
    conn.close()

def ambil_semua_agenda():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT id, jadwal, kegiatan FROM agenda")
    data = c.fetchall()
    conn.close()
    return data

def hapus_agenda(id_agenda):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("DELETE FROM agenda WHERE id=?", (id_agenda,))
    conn.commit()
    conn.close()
