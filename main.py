"""
main.py
Entry point utama untuk aplikasi Telegram Bot Rafsistant.
Menghubungkan seluruh modul (API Kampus, Database Lokal, Google API) 
dan menangani instruksi/perintah langsung dari pengguna.
"""

import os
import pytz
from datetime import datetime, time

from api_kampus import tarik_jadwal_uts
from tugas_db import init_tugas_db, tambah_tugas, ambil_semua_tugas, hapus_tugas
from google_api import tambah_tugas_ke_google, tambah_agenda_ke_google, catat_ke_sheets, baca_dari_sheets
from agenda_db import init_agenda_db, tambah_agenda, ambil_semua_agenda, hapus_agenda

# Memuat konfigurasi aman dari settings.py
from settings import (
    BOT_TOKEN, 
    CHAT_ID_BAGINDA, 
    ID_SPREADSHEET, 
    NIM_KAMPUS, 
    PASSWORD_KAMPUS
)

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

async def post_init(application: Application):
    """Mendaftarkan menu bantuan command bot di antarmuka Telegram."""
    await application.bot.set_my_commands([
        ("menu", "Buka gulungan panduan & fitur"),
        ("jadwal", "Cek jadwal akademik aktif"),
        ("catat", "Titip catatan tugas"),
        ("tugasku", "Lihat tumpukan tugas"),
        ("selesai", "Lenyapkan tugas berdasarkan ID"),
        ("agenda", "Atur jadwal pertemuan"),
        ("agendaku", "Lihat agenda penting"),
        ("coretagenda", "Batalkan agenda berdasarkan ID"),
        ("uang", "Catat mutasi keuangan"),
        ("uangku", "Cek riwayat buku kas")
    ])

# ==========================================
# KOMPARTEMEN HANDLER PERINTAH
# ==========================================

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    pesan = f"Salam, {user.first_name}! Asisten virtual siap melayani konfigurasi harian Anda. ⚙️\n\nKetik /menu untuk melihat daftar perintah yang tersedia."
    await update.message.reply_text(pesan)

async def morning_briefing(context: ContextTypes.DEFAULT_TYPE):
    """Tugas otomatis harian untuk mengirim rangkuman agenda pagi."""
    tugas = ambil_semua_tugas()
    agenda = ambil_semua_agenda()
    
    pesan = "🌅 *MORNING BRIEFING SYSTEM* 🌅\n\n"
    pesan += "Berikut adalah rangkuman tugas dan agenda Anda hari ini:\n\n"
    
    pesan += "📝 *TUGAS TERTUNDA:*\n"
    if tugas:
        for t in tugas:
            pesan += f"• {t[1]}\n"
    else:
        pesan += "• Sistem mendeteksi tidak ada tugas tertunda.\n"
        
    pesan += "\n🗓️ *AGENDA MENDATANG:*\n"
    if agenda:
        for a in agenda:
            pesan += f"• 📅 {a[1]} - 📌 {a[2]}\n"
    else:
        pesan += "• Tidak ada agenda yang dijadwalkan hari ini.\n"
        
    pesan += "\n_Semoga hari Anda produktif!_"
    
    if CHAT_ID_BAGINDA:
        await context.bot.send_message(chat_id=CHAT_ID_BAGINDA, text=pesan, parse_mode='Markdown')

async def uang_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    teks = " ".join(context.args)
    if "-" not in teks:
        await update.message.reply_text("❌ Format salah. Gunakan: /uang [keluar/masuk] [nominal] [kategori] - [keterangan]")
        return

    try:
        data_kiri, keterangan = [p.strip() for p in teks.split("-", 1)]
        parts = data_kiri.split()
        tipe = parts[0].upper() 
        jumlah = parts[1] 
        kategori = " ".join(parts[2:]) 
        tanggal = datetime.now().strftime("%d/%m/%Y %H:%M")

        if catat_ke_sheets(ID_SPREADSHEET, tanggal, tipe, kategori, jumlah, keterangan):
            await update.message.reply_text(f"✅ Data tersimpan di Cloud Database!\n📊 Tipe: {tipe} (Rp {jumlah})\n🗂️ Kategori: {kategori}\n📝 Ket: {keterangan}")
        else:
            await update.message.reply_text("⚠️ Kesalahan sistem: Gagal menghubungkan ke Google Sheets.")
    except Exception as e:
        await update.message.reply_text("⚠️ Kesalahan sistem: Format instruksi tidak dapat diproses.")

async def catat_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    teks = " ".join(context.args)
    if not teks:
        await update.message.reply_text("⚠️ Anda belum memasukkan detail tugas.")
        return
    tugas_final = f"{teks.split('-')[0].strip()} (Tenggat: {teks.split('-')[1].strip()})" if "-" in teks else teks
    
    tambah_tugas(tugas_final)
    tambah_tugas_ke_google(tugas_final)
    await update.message.reply_text(f"✅ Tugas berhasil dicatat ke sistem:\n• {tugas_final}")

async def agenda_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    teks = " ".join(context.args)
    if "-" not in teks:
        await update.message.reply_text("❌ Format salah. Gunakan: /agenda [waktu] - [kegiatan]")
        return
    t, k = [p.strip() for p in teks.split("-", 1)]
    
    tambah_agenda(t, k)
    link = tambah_agenda_ke_google(t, k)
    
    msg = f"✅ Agenda '{k}' telah ditambahkan ke database."
    if link: msg += f"\n🔗 [Sinkronisasi Google Calendar]({link})"
    await update.message.reply_text(msg, parse_mode='Markdown', disable_web_page_preview=True)

async def jadwal_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not NIM_KAMPUS or not PASSWORD_KAMPUS:
        await update.message.reply_text("⚠️ Kredensial kampus belum diatur di sistem.")
        return
        
    await update.message.reply_text("⏳ Menginisiasi koneksi ke server akademik...")
    hasil = tarik_jadwal_uts(NIM_KAMPUS, PASSWORD_KAMPUS)
    await update.message.reply_text(hasil, parse_mode='Markdown')

async def tugasku_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    dt = ambil_semua_tugas()
    msg = "📝 *STATUS TUGAS*\n\n" + "\n".join([f"ID {t[0]}: {t[1]}" for t in dt]) if dt else "✅ Seluruh antrean tugas telah diselesaikan."
    await update.message.reply_text(msg, parse_mode='Markdown')

async def agendaku_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    da = ambil_semua_agenda()
    msg = "🗓️ *AGENDA TERJADWAL*\n\n" + "\n".join([f"ID {a[0]} | {a[1]}: {a[2]}" for a in da]) if da else "🗓️ Tidak ada agenda yang tersimpan."
    await update.message.reply_text(msg, parse_mode='Markdown')

async def selesai_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("⚠️ Instruksikan ID tugas yang ingin diselesaikan.")
        return
    try:
        id_tugas = int(context.args[0])
        hapus_tugas(id_tugas)
        await update.message.reply_text(f"✅ Tugas dengan ID {id_tugas} telah dihapus dari antrean.")
    except ValueError:
        await update.message.reply_text("❌ Parameter tidak valid. Pastikan ID menggunakan format numerik.")

async def coretagenda_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("⚠️ Instruksikan ID agenda yang ingin dibatalkan.")
        return
    try:
        id_agenda = int(context.args[0])
        hapus_agenda(id_agenda)
        await update.message.reply_text(f"✅ Agenda dengan ID {id_agenda} telah dibatalkan.")
    except ValueError:
        await update.message.reply_text("❌ Parameter tidak valid. Pastikan ID menggunakan format numerik.")

async def menu_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pesan = "📜 *MANUAL PENGGUNAAN SISTEM* 📜\n\n"
    
    pesan += "🎓 *Integrasi Akademik*\n"
    pesan += "• `/jadwal` - Sinkronisasi jadwal sistem akademik\n\n"
    
    pesan += "📝 *Manajemen Tugas*\n"
    pesan += "• `/catat [tugas] - [tenggat]` - Entri tugas baru\n"
    pesan += "• `/tugasku` - Tampilkan daftar tugas\n