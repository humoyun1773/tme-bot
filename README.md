# Musiqa & Media Yuklovchi Telegram Bot 🎵📥

Foydalanuvchilarga turli ijtimoiy tarmoqlardan (YouTube, Instagram, TikTok va b.) video va audio (MP3) yuklab beruvchi, shuningdek qo'shiq nomi bo'yicha tezkor qidiruvchi universal Telegram bot.

---

## 🚀 Asosiy Imkoniyatlar

### 1. 🎧 Qo'shiq nomi bo'yicha qidirish (Matnli qidiruv)
- Qo'shiq yoki ijrochi nomini yozing (masalan: `Ummon - Sensiz` yoki `Konsta - Odamlar`).
- Bot eng sara 5 ta natijani zamonaviy ro'yxat va `[ 1️⃣ ] [ 2️⃣ ] [ 3️⃣ ] [ 4️⃣ ] [ 5️⃣ ]` ixcham tugmalar bilan taqdim etadi.
- Tanlangan qo'shiq yuqori sifatli MP3 formatida, albom muqovasi (cover art) va ID3 teglari bilan yuboriladi.

### 2. 📥 Havola (Link) orqali yuklash
- 🔴 **YouTube**: Video sifatlari (`720p HD`, `1080p FHD`, `360p`) hamda Audio bitratelari (`128 kbps`, `192 kbps`, `320 kbps HD`) tanlash imkoniyati.
- ⏱ **15 daqiqadan ortiq** videolar uchun avtomatik ogohlantirish.
- 📷 **Instagram**: Reels, Post, Karusel va Stories.
- 🎵 **TikTok**: Suv belgisiz (without watermark) video va musiqa.
- 🐦 **Twitter / X, Pinterest**: Video va rasmlar.

### 3. ⭐ Tarix va Sevimlilar
- 📜 **/history**: Foydalanuvchi oxirgi yuklab olgan 10 ta qo'shiqlari ro'yxati va bir bosishda qayta yuklab olish.
- ❤️ **/favorites**: Sevimli qo'shiqlar ro'yxati. Har bir yuborilgan audio ostida `❤️ Sevimlilarga qo'shish` tugmasi mavjud.

---

## 📋 Buyruqlar (Commands)

| Buyruq | Vazifasi |
|---|---|
| `/start` | Botni ishga tushirish va qo'llanma |
| `/help` | Botdan qanday foydalanish bo'yicha yo'riqnoma |
| `/history` | Oxirgi yuklangan qo'shiqlar tarixi |
| `/favorites` | Sevimli qo'shiqlar ro'yxati |
| `/stats` | (Admin uchun) foydalanuvchilar va yuklamalar statistikasi |
| `/broadcast` | (Admin uchun) barcha foydalanuvchilarga xabar yuborish |

---

## 🛠 Texnik Stack

- **Python 3.11+**
- **aiogram 3.x** (Asinxron Telegram Bot framework)
- **yt-dlp** (Eng so'nggi YouTube/TikTok/Instagram ekstraktori)
- **FFmpeg** / **imageio-ffmpeg** (Audio konvertatsiya va format birlashtirish)
- **mutagen** (ID3 teglar va muqova rasmlarini yozish)
- **aiosqlite** (Asinxron SQLite ma'lumotlar bazasi)

---

## ⚙️ O'rnatish va Ishga tushirish

```bash
# 1. Klonlash
git clone https://github.com/humoyun1773/tme-bot.git
cd tme-bot

# 2. Virtual muhit
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate # Linux/Mac

# 3. Paketlarni o'rnatish
pip install -r requirements.txt

# 4. .env sozlash
cp .env.example .env
# .env fayliga BOT_TOKEN va ADMIN_IDS kiriting

# 5. Ishga tushirish
python main.py
```

---

## 📄 Litsenziya
MIT License
