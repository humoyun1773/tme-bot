# Universal Media Downloader & Music Bot 📥🎵

Telegram orqali YouTube, Instagram, TikTok va boshqa ijtimoiy tarmoqlardan video, audio (MP3), rasm va karusel kontentlarini yuklab beruvchi, shuningdek qo'shiq nomi bo'yicha qidiruvchi universal bot.

---

## 🚀 Imkoniyatlar

- 🔎 **Qo'shiq nomi bo'yicha qidirish (Matnli qidiruv)**:
  - Shunchaki qo'shiq nomi yoki ijrochisini yozing (masalan: `Ummon - Sensiz` yoki `Konsta`)
  - Eng mos 5 ta natija inline tugmalar shaklida chiqariladi
  - Qo'shiqni to'liq MP3 formatida, albom muqovasi (cover art) va ijrochi teglari (ID3) bilan yuklab beradi
- 🔴 **YouTube**:
  - Sifat tanlash imkoniyati: `360p`, `480p`, `720p HD`, `1080p FHD`
  - Faqat audio / musiqa (`MP3`) qilib yuklab olish
  - YouTube Shorts videolari
- 📷 **Instagram**:
  - Reels videolari
  - Postlar (rasm va videolar)
  - Karusel (bir nechta rasm/videolarni bitta albom qilib yuborish)
  - Stories (ochiq profillar uchun)
- 🎵 **TikTok**:
  - Videolarni **suv belgisiz (without watermark)** yuklash
  - Musiqa / audiosini ajratib olish
- 🌐 **Boshqa tarmoqlar**: Twitter / X, Pinterest, SoundCloud, Facebook va boshqalar
- 📊 **Admin panel**: Foydalanuvchilar soni, platformalar bo'yicha statistika (`/stats`) va barchaga xabar yuborish (`/broadcast`)
- 🛡️ **Xavfsiz va toza**: Yuklangan barcha vaqtinchalik fayllar foydalanuvchiga yuborilgach avtomatik o'chiriladi.

---

## 🛠 Texnologiyalar

- **Python 3.11+**
- **aiogram 3.x** (Asinxron Telegram Bot framework)
- **yt-dlp** (Eng so'nggi media yuklovchi yadro va qidiruv tizimi)
- **FFmpeg** / **imageio-ffmpeg** (Audio konvertatsiya va video formatlarni birlashtirish)
- **mutagen** (MP3 ID3 teglar va muqova rasmlarini joylash)
- **aiosqlite** (Asinxron SQLite ma'lumotlar bazasi)

---

## ⚙️ O'rnatish va Ishga tushirish

### 1. Repozitoriyni yuklab olish (Clone)
```bash
git clone https://github.com/humoyun1773/tme-bot.git
cd tme-bot
```

### 2. Virtual muhit yaratish va faollashtirish
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux / MacOS
python3 -m venv venv
source venv/bin/activate
```

### 3. Kerakli paketlarni o'rnatish
```bash
pip install -r requirements.txt
```

### 4. Sozlamalar (.env)
`.env.example` faylidan `.env` nusxasini oling:
```bash
cp .env.example .env
```
`.env` faylini ochib, o'z bot tokeningiz va admin ID laringizni kiriting:
```env
BOT_TOKEN=your_telegram_bot_token_here
ADMIN_IDS=123456789
MAX_FILE_SIZE_MB=50
```

### 5. Botni ishga tushirish
```bash
python main.py
```

---

## 📋 Bot Buyruqlari

| Buyruq | Tavsif | Kimlar uchun |
|---|---|---|
| `/start` | Botni ishga tushirish va ma'lumot olish | Barcha |
| `/help` | Botdan foydalanish qo'llanmasi | Barcha |
| `/stats` | Foydalanuvchilar va yuklamalar statistikasi | Admin |
| `/broadcast` | Barcha foydalanuvchilarga xabar yuborish | Admin |

---

## 📄 Litsenziya
Ushbu loyiha MIT litsenziyasi asosida tarqatiladi.
