import os
from dotenv import load_dotenv

# Load variabel dari file .env
load_dotenv()

# Identitas Rafsistant & Baginda Ali
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
CHAT_ID_BAGINDA = os.getenv("CHAT_ID", "1747981497")

if not BOT_TOKEN:
    print("⚠️ Peringatan: BOT_TOKEN belum disetting! Cek file .env kamu.")
    exit(1)