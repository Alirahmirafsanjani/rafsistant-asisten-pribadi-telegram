import os
import pytz
from datetime import datetime, time

from api_kampus import tarik_jadwal_uts
from tugas_db import init_tugas_db, tambah_tugas, ambil_semua_tugas, hapus_tugas
from google_api import tambah_tugas_ke_google, tambah_agenda_ke_google, catat_ke_sheets, baca_dari_sheets
from gitignore.agenda_db import init_agenda_db, tambah_agenda, ambil_semua_agenda, hapus_agenda
from settings import BOT_TOKEN, CHAT_ID_BAGINDA

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# === SINGGASANA KONFIGURASI ===
ID_SPREADSHEET = "ID_SPREADSHEET_KAMU"  # Ganti dengan ID spreadsheet yang benar
PASSWORD_ALMA = "PASSWORD_ALMA_KAMU"  # Ganti dengan password Alma Ata yang benar

async def post_init(application: Application):
    await application.bot.set_my_commands([
        ("menu", "Buka gulungan panduan & fitur"),
        ("jadwal", "Cek jadwal UTS Baginda"),
        ("catat", "Titip catatan tugas"),
        ("tugasku", "Lihat tumpukan tugas"),
        ("selesai", "Lenyapkan tugas"),
        ("agenda", "Atur jadwal pertemuan"),
        ("agendaku", "Lihat agenda penting"),
        ("coretagenda", "Batalkan agenda"),
        ("uang", "Catat harta keluar/masuk"),
        ("uangku", "Cek riwayat buku kas")
    ])

# --- HANDLER START (Buatan Baru) ---
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    pesan = f"Ampun {user.first_name}, hamba Rafsistant siap melayani Baginda! 👑\n\nKetik /menu untuk melihat daftar kesaktian hamba."
    await update.message.reply_text(pesan)

# --- LAPORAN PAGI (06:00 WIB) ---
async def morning_briefing(context: ContextTypes.DEFAULT_TYPE):
    tugas = ambil_semua_tugas()
    agenda = ambil_semua_agenda()
    
    pesan = "🌅 *SELAMAT PAGI, BAGINDA!* 🌅\n\n"
    pesan += "Hamba menghadap untuk melaporkan ringkasan tugas dan agenda Baginda hari ini:\n\n"
    
    pesan += "📝 *TUGAS YANG MENUNGGU:*\n"
    if tugas:
        for t in tugas:
            pesan += f"• {t[1]}\n"
    else:
        pesan += "• Bersih! Tidak ada tugas yang menumpuk, Baginda.\n"
        
    pesan += "\n🗓️ *AGENDA MENDATANG:*\n"
    if agenda:
        for a in agenda:
            pesan += f"• 📅 {a[1]} - 📌 {a[2]}\n"
    else:
        pesan += "• Kosong! Hari ini jadwal Baginda aman.\n"
        
    pesan += "\nSelamat menjalani hari baginda, jangan lupa 76 Apelnya, semoga selalu dilancarkan! 👑🔥"
    
    await context.bot.send_message(chat_id=CHAT_ID_BAGINDA, text=pesan, parse_mode='Markdown')

# --- HANDLER KEUANGAN ---
async def uang_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    teks = " ".join(context.args)
    if "-" not in teks:
        await update.message.reply_text("Mohon maaf Baginda, formatnya: /uang keluar 50k jajan - beli sate")
        return

    try:
        data_kiri, keterangan = [p.strip() for p in teks.split("-", 1)]
        parts = data_kiri.split()
        tipe = parts[0].upper() 
        jumlah = parts[1] 
        kategori = " ".join(parts[2:]) 
        tanggal = datetime.now().strftime("%d/%m/%Y %H:%M")

        if catat_ke_sheets(ID_SPREADSHEET, tanggal, tipe, kategori, jumlah, keterangan):
            await update.message.reply_text(f"Harta Baginda telah hamba catat di Sheets! 💰\n📊 {tipe}: Rp {jumlah}\n🗂️ Kategori: {kategori}\n📝 Ket: {keterangan}")
        else:
            await update.message.reply_text("Waduh Baginda, hamba gagal konek ke Sheets. Cek lagi kuncinya ya.")
    except:
        await update.message.reply_text("Formatnya salah, Baginda. Hamba bingung bacanya.")

# --- HANDLER TUGAS ---
async def catat_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    teks = " ".join(context.args)
    if not teks:
        await update.message.reply_text("Ampun Baginda, catatannya mana? 🙏")
        return
    tugas_final = f"{teks.split('-')[0].strip()} (Tenggat: {teks.split('-')[1].strip()})" if "-" in teks else teks
    tambah_tugas(tugas_final)
    tambah_tugas_ke_google(tugas_final)
    await update.message.reply_text(f"Beres, Baginda! Tugasnya sudah hamba amankan:\n• {tugas_final}")

# --- HANDLER AGENDA ---
async def agenda_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    teks = " ".join(context.args)
    if "-" not in teks:
        await update.message.reply_text("Formatnya kurang tepat, Baginda. Coba: /agenda Besok - Rapat Penting")
        return
    t, k = [p.strip() for p in teks.split("-", 1)]
    tambah_agenda(t, k)
    link = tambah_agenda_ke_google(t, k)
    msg = f"Siap Baginda, agenda '{k}' sudah hamba masukkan ke kalender."
    if link: msg += f"\n🔗 [Cek di sini]({link})"
    await update.message.reply_text(msg, parse_mode='Markdown', disable_web_page_preview=True)

# --- HANDLER LAINNYA ---
async def jadwal_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("⏳ Menarik jadwal UTS Baginda dari Alma Ata...")
    hasil = tarik_jadwal_uts("243100400", PASSWORD_ALMA)
    await update.message.reply_text(hasil, parse_mode='Markdown')

async def tugasku_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    dt = ambil_semua_tugas()
    msg = "📝 *DAFTAR TUGAS BAGINDA*\n\n" + "\n".join([f"ID {t[0]}: {t[1]}" for t in dt]) if dt else "🎉 Semua tugas kelar, Baginda!"
    await update.message.reply_text(msg, parse_mode='Markdown')

async def agendaku_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    da = ambil_semua_agenda()
    msg = "🗓️ *AGENDA PENTING BAGINDA*\n\n" + "\n".join([f"ID {a[0]} | {a[1]}: {a[2]}" for a in da]) if da else "🗓️ Kosong, Baginda!"
    await update.message.reply_text(msg, parse_mode='Markdown')

async def selesai_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Ampun Baginda, ID tugas nomor berapa yang mau dihapus? Contoh: /selesai 1")
        return
    try:
        id_tugas = int(context.args[0])
        hapus_tugas(id_tugas)
        await update.message.reply_text(f"Sesuai titah! Tugas ID {id_tugas} telah hamba lenyapkan dari pandangan Baginda. 🧹")
    except ValueError:
        await update.message.reply_text("Maaf Baginda, format ID salah. Pastikan menggunakan angka.")

async def coretagenda_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Ampun Baginda, ID agenda nomor berapa yang batal? Contoh: /coretagenda 1")
        return
    try:
        id_agenda = int(context.args[0])
        hapus_agenda(id_agenda)
        await update.message.reply_text(f"Siap Baginda! Agenda ID {id_agenda} sudah hamba coret dari daftar jadwal. 🗑️")
    except ValueError:
        await update.message.reply_text("Maaf Baginda, format ID salah. Pastikan menggunakan angka.")

async def menu_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pesan = "📜 *GULUNGAN TITAH BAGINDA* 📜\n\n"
    pesan += "Berikut adalah daftar kesaktian hamba:\n\n"
    
    pesan += "🎓 *AKADEMIK*\n"
    pesan += "• `/jadwal` - Cek jadwal UTS Alma Ata\n\n"
    
    pesan += "📝 *MANAJEMEN TUGAS*\n"
    pesan += "• `/catat [tugas] - [tenggat]` - Tambah tugas\n"
    pesan += "• `/tugasku` - Lihat semua tugas\n"
    pesan += "• `/selesai [ID]` - Lenyapkan tugas\n\n"
    
    pesan += "🗓️ *MANAJEMEN AGENDA*\n"
    pesan += "• `/agenda [waktu] - [kegiatan]` - Tambah agenda\n"
    pesan += "• `/agendaku` - Lihat semua agenda\n"
    pesan += "• `/coretagenda [ID]` - Batalkan agenda\n\n"
    
    pesan += "💰 *BRANKAS KEUANGAN*\n"
    pesan += "• `/uang [masuk/keluar] [jumlah] [kategori] - [ket]` - Catat mutasi\n"
    pesan += "• `/uangku` - Intip riwayat harta terakhir\n\n"
    
    pesan += "⚠️ *PANDUAN FORMAT PENTING* ⚠️\n"
    pesan += "1. Tanda strip (`-`) adalah kunci pemisah! Wajib ada saat mencatat tugas, agenda, atau uang.\n"
    pesan += "2. ID Tugas/Agenda berupa angka, didapat dari perintah `/tugasku` atau `/agendaku`.\n"
    pesan += "3. Jangan lupakan spasi sebelum dan sesudah tanda strip."
    
    await update.message.reply_text(pesan, parse_mode='Markdown')

async def uangku_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("⏳ Sebentar Baginda, hamba sedang membuka brankas Google Sheets...")
    data = baca_dari_sheets(ID_SPREADSHEET)
    
    if data is None:
        await update.message.reply_text("Ampun Baginda, hamba gagal membuka brankas. Kuncinya macet!")
        return
    if not data:
        await update.message.reply_text("Buku kas Baginda masih kosong melompong! 💸")
        return
        
    pesan = "💰 *5 RIWAYAT HARTA TERAKHIR BAGINDA* 💰\n\n"
    for baris in data[-5:]: 
        if len(baris) >= 4: 
            tanggal = baris[0] if len(baris) > 0 else "-"
            tipe = baris[1] if len(baris) > 1 else "-"
            kategori = baris[2] if len(baris) > 2 else "-"
            jumlah = baris[3] if len(baris) > 3 else "0"
            ket = baris[4] if len(baris) > 4 else "-"
            
            icon = "🟢" if tipe.upper() == "MASUK" else "🔴"
            pesan += f"{icon} *{tipe.upper()}* (Rp {jumlah})\n"
            pesan += f"📅 {tanggal}\n"
            pesan += f"🗂️ {kategori} - {ket}\n"
            pesan += "〰️〰️〰️〰️〰️〰️\n"
            
    pesan += "\n🔗 Untuk selengkapnya, silakan cek langsung di Google Sheets Baginda."
    await update.message.reply_text(pesan, parse_mode='Markdown')

def main():
    # Inisialisasi Database Kamu Sendiri
    init_tugas_db()
    init_agenda_db()
    
    app = Application.builder().token(BOT_TOKEN).post_init(post_init).build()
    
    # --- Setup Alarm Pagi (06:00 WIB) ---
    wib = pytz.timezone('Asia/Jakarta')
    waktu_pagi = time(hour=6, minute=0, second=0, tzinfo=wib)
    app.job_queue.run_daily(morning_briefing, time=waktu_pagi)
    
    # Daftarkan Handler Milikmu
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("jadwal", jadwal_command))
    app.add_handler(CommandHandler("catat", catat_command))
    app.add_handler(CommandHandler("tugasku", tugasku_command))
    app.add_handler(CommandHandler("selesai", selesai_command))
    app.add_handler(CommandHandler("agenda", agenda_command))
    app.add_handler(CommandHandler("agendaku", agendaku_command))
    app.add_handler(CommandHandler("coretagenda", coretagenda_command))
    app.add_handler(CommandHandler("uang", uang_command))
    app.add_handler(CommandHandler("menu", menu_command))
    app.add_handler(CommandHandler("uangku", uangku_command))
    
    print("Rafsistant siap melayani Baginda...")
    app.run_polling()

if __name__ == "__main__": 
    main()
    