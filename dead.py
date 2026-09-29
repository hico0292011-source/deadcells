import os
import asyncio
import logging
from aiohttp import web
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.types import WebAppInfo, InlineKeyboardMarkup, InlineKeyboardButton

# Loglarni sozlash
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("DeadCellsBot")

# Bot Token va Render External URL
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8745387169:AAGmxnJmX7ISJj4dojWZbqWZRDbDEBl2624")
RENDER_URL = os.environ.get("RENDER_EXTERNAL_URL", "https://anonbot-1.onrender.com")

# HTTPS formatini tekshirish
if not RENDER_URL.startswith("https://"):
    RENDER_URL = f"https://{RENDER_URL.replace('http://', '')}"

# Bot va Dispatcher
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


@dp.message(CommandStart())
async def start_handler(message: types.Message):
    """ /start bosilganda Mini App tugmasini yuborish """
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="⚔️ Dead Cells 2D - O'yinni Boshlash 🎮",
                web_app=WebAppInfo(url=RENDER_URL)
            )
        ]
    ])
    
    caption = (
        f"🔥 <b>DEAD CELLS 2D - DARK EDITION</b> 🔥\n\n"
        f"Salom, <b>{message.from_user.first_name}</b>!\n"
        f"Zindon olamiga xush kelibsiz. Qilichingizni qayrang va monsterlarni tor-mor eting!\n\n"
        f"👇 <i>O'yinni ochish uchun pastdagi tugmani bosing:</i>"
    )
    
    await message.answer(caption, reply_markup=keyboard, parse_mode="HTML")


# --- WEB SERVER ROUTES ---

async def handle_index(request):
    """ HTML5 O'yin faylini (index.html) brauzer/Telegram WebApp ga uzatish """
    if os.path.exists("index.html"):
        return web.FileResponse("index.html", headers={"Content-Type": "text/html; charset=utf-8"})
    return web.Response(text="<h1>❌ index.html fayli topilmadi!</h1>", content_type="text/html", status=404)


async def handle_ping(request):
    """ Render botini 24/7 poylab turish va cron-job.org uchun ping marshruti """
    return web.Response(text="OK", status=200)


async def main():
    logger.info("🚀 WebApp Server va Telegram Bot ishga tushmoqda...")

    # Aiohttp Web Server sozlamalari
    app = web.Application()
    app.router.add_get('/', handle_index)
    app.router.add_get('/ping', handle_ping)
    
    runner = web.AppRunner(app)
    await runner.setup()
    
    port = int(os.environ.get("PORT", 8080))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    logger.info(f"🌐 Web-server Port {port} da ishga tushdi (URL: {RENDER_URL})")

    # Bot Polling va Serverni parallel yurgizish
    try:
        await dp.start_polling(bot)
    finally:
        await runner.cleanup()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("🛑 Bot to'xtatildi.")
