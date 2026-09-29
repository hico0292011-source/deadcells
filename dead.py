import os
import asyncio
import logging
from aiohttp import web
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.types import WebAppInfo, InlineKeyboardMarkup, InlineKeyboardButton

# Loglarni sozlash (Xatoliklarni ko'rib turish uchun)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("HillClimbBot")

# Bot Token va Render External URL (O'zgaruvchilarni olish)
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8745387169:AAGmxnJmX7ISJj4dojWZbqWZRDbDEBl2624")
RENDER_URL = os.environ.get("RENDER_EXTERNAL_URL", "https://anonbot-1.onrender.com")

# URL formati to'g'riligini tekshirish
if not RENDER_URL.startswith("https://"):
    RENDER_URL = f"https://{RENDER_URL.replace('http://', '')}"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

@dp.message(CommandStart())
async def start_handler(message: types.Message):
    """ /start buyrug'i bosilganda yuboriladigan xabar """
    
    # O'yinni ochuvchi Mini App tugmasi
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="🚙 Hill Climb Racing - O'ynash",
                web_app=WebAppInfo(url=RENDER_URL)
            )
        ]
    ])
    
    caption = (
        f"🏔 <b>HILL CLIMB RACING</b> 🚙\n\n"
        f"Salom, <b>{message.from_user.first_name}</b>!\n"
        f"Tog'lar va tepaliklar bo'ylab harakatlaning, yoqilg'i yig'ing va mashinani ag'darib yubormaslikka harakat qiling!\n\n"
        f"👇 <i>O'yinni boshlash uchun pastdagi tugmani bosing:</i>"
    )
    
    await message.answer(caption, reply_markup=keyboard, parse_mode="HTML")


# --- WEB SERVER QISMI ---

async def handle_index(request):
    """ index.html faylini web-server orqali ulashish """
    if os.path.exists("index.html"):
        return web.FileResponse("index.html", headers={"Content-Type": "text/html; charset=utf-8"})
    return web.Response(text="<h1>❌ index.html topilmadi! O'yin faylini joylang.</h1>", content_type="text/html", status=404)

async def handle_ping(request):
    """ cron-job.org orqali botni 24/7 uyg'oq tutish uchun /ping marshruti """
    return web.Response(text="Server ishlayapti 🟢", status=200)

async def main():
    logger.info("🚀 Server va Bot ishga tushirilmoqda...")

    # Aiohttp Web Serverni sozlash
    app = web.Application()
    app.router.add_get('/', handle_index)
    app.router.add_get('/ping', handle_ping)
    
    runner = web.AppRunner(app)
    await runner.setup()
    
    port = int(os.environ.get("PORT", 8080))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    logger.info(f"🌐 Web-server {port}-portda ishlamoqda. Manzil: {RENDER_URL}")

    # Botni ishga tushirish
    try:
        await dp.start_polling(bot)
    finally:
        await runner.cleanup()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("🛑 Bot to'xtatildi.")
