import telebot
import instaloader
import os
import json
from datetime import datetime

TOKEN = "token_qoying"
DOWNLOAD_FOLDER = "downloads"
LOG_FILE = "bot_log.json"
STATS_FILE = "bot_stats.json"

bot = telebot.TeleBot(TOKEN)
L = instaloader.Instaloader()

if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)

if not os.path.exists(STATS_FILE):
    with open(STATS_FILE, "w") as f:
        json.dump({}, f)

def log_event(user_id, username, message, status):
    log_data = {
        "time": str(datetime.now()),
        "user_id": user_id,
        "username": username,
        "message": message,
        "status": status
    }
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r") as f:
            logs = json.load(f)
    else:
        logs = []
    logs.append(log_data)
    with open(LOG_FILE, "w") as f:
        json.dump(logs, f, indent=4)

def update_stats(user_id):
    with open(STATS_FILE, "r") as f:
        stats = json.load(f)
    stats[str(user_id)] = stats.get(str(user_id), 0) + 1
    with open(STATS_FILE, "w") as f:
        json.dump(stats, f, indent=4)

def clean_download_folder():
    for f in os.listdir(DOWNLOAD_FOLDER):
        file_path = os.path.join(DOWNLOAD_FOLDER, f)
        if os.path.isfile(file_path):
            os.remove(file_path)

@bot.message_handler(commands=['start'])
def start_message(message):
    bot.reply_to(message, "Salom! Instagram video linkini yuboring.\n\nFoydalanish:\n- Faqat video post yoki reel linkini yuboring.\n- Video topilsa, sizga yuboriladi.")
    log_event(message.chat.id, message.from_user.username, "/start", "OK")

@bot.message_handler(commands=['help'])
def help_message(message):
    bot.reply_to(message, "Bot funksiyalari:\n- Link yuborish -> Video yuboriladi\n- /stats -> Sizning video so‘rovlar soni")
    log_event(message.chat.id, message.from_user.username, "/help", "OK")

@bot.message_handler(commands=['stats'])
def stats_message(message):
    with open(STATS_FILE, "r") as f:
        stats = json.load(f)
    user_stats = stats.get(str(message.chat.id), 0)
    bot.reply_to(message, f"Siz so‘ragan videolar soni: {user_stats}")
    log_event(message.chat.id, message.from_user.username, "/stats", f"{user_stats} videos")

@bot.message_handler(func=lambda m: True)
def download_instagram_video(message):
    try:
        shortcode = message.text.split("/")[-2]
        post = instaloader.Post.from_shortcode(L.context, shortcode)
        if post.is_video:
            L.download_post(post, DOWNLOAD_FOLDER)
            video_files = [f for f in os.listdir(DOWNLOAD_FOLDER) if f.endswith(".mp4")]
            if not video_files:
                bot.reply_to(message, "Video yuklashda xato!")
                log_event(message.chat.id, message.from_user.username, message.text, "Video yuklash xato")
                return
            for file in video_files:
                video_path = os.path.join(DOWNLOAD_FOLDER, file)
                with open(video_path, "rb") as v:
                    bot.send_video(message.chat.id, v)
                os.remove(video_path)
            update_stats(message.chat.id)
            log_event(message.chat.id, message.from_user.username, message.text, "Video yuborildi")
        else:
            bot.reply_to(message, "Bu post video emas!")
            log_event(message.chat.id, message.from_user.username, message.text, "Rasm post")
    except Exception as e:
        bot.reply_to(message, f"Xato yuz berdi: {e}")
        log_event(message.chat.id, message.from_user.username, message.text, f"Xato: {e}")
    finally:
        clean_download_folder()

bot.polling(none_stop=True)
