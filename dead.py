import os
import asyncio
import logging
import random
import json
from aiohttp import web
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

# Logging sozlamalari
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Bot Tokeni
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8745387169:AAGmxnJmX7ISJj4dojWZbqWZRDbDEBl2624")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Game Data & Assets (Dead Cells / Skul uslubida)
CLASSES = {
    "knight": {"name": "🗡️ Ritsar", "damage": (15, 25), "skill_dmg": (35, 50), "skill": "Qilich zarbasi"},
    "ninja": {"name": "🥷 Soya Ninjasi", "damage": (20, 30), "skill_dmg": (45, 65), "skill": "Kritik Pichoq"},
    "mage": {"name": "🧙‍♂️ Kimyogar", "damage": (12, 22), "skill_dmg": (40, 70), "skill": "Kislota portlashi"},
    "reaper": {"name": "💀 Azroil Kalla", "damage": (25, 35), "skill_dmg": (50, 85), "skill": "O'lim O'rog'i"}
}

ENEMIES = [
    {"name": "🧟 Zombi Jangchi", "hp": 70, "damage": (10, 16), "cells": 15},
    {"name": "🏹 Zaharli Kamonchi", "hp": 55, "damage": (12, 20), "cells": 20},
    {"name": "🛡️ Qizil Soqchi", "hp": 90, "damage": (14, 22), "cells": 28},
    {"name": "🐉 Ishkencechi Mutant (Boss)", "hp": 150, "damage": (18, 30), "cells": 60}
]

DATA_FILE = "dead_game_data.json"

def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Faylni o'qishda xatolik: {e}")
            return {}
    return {}

def save_data(data):
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Faylga saqlashda xatolik: {e}")

user_data = load_data()

def get_user(user_id):
    str_id = str(user_id)
    if str_id not in user_data:
        user_data[str_id] = {
            "max_hp": 100,
            "hp": 100,
            "cells": 0,           # Dead Cells dagi "Hujayralar" (doimiy valyuta)
            "potions": 2,         # Zelye
            "cls": "knight",
            "unlocked": ["knight"],
            "in_battle": False,
            "enemy": None
        }
        save_data(user_data)
    return user_data[str_id]

# Keyboards
def get_battle_keyboard(user):
    builder = InlineKeyboardBuilder()
    builder.button(text="⚔️ Oddiy Hujum", callback_data="act_attack")
    builder.button(text="⚡ Maxsus Mahorat", callback_data="act_skill")
    builder.button(text=f"🧪 Zelye Ichish ({user['potions']})", callback_data="act_heal")
    builder.button(text="🔄 Sinfi (Kallani) O'zgartirish", callback_data="act_swap")
    builder.adjust(2, 2)
    return builder.as_markup()

def get_swap_keyboard(user):
    builder = InlineKeyboardBuilder()
    for c_key in user["unlocked"]:
        c_info = CLASSES[c_key]
        builder.button(text=c_info["name"], callback_data=f"set_cls_{c_key}")
    builder.adjust(2)
    return builder.as_markup()

@dp.message(Command("start"))
async def start_cmd(message: types.Message):
    user = get_user(message.from_user.id)
    cls_info = CLASSES[user["cls"]]
    
    await message.answer(
        f"🩸 <b>DEAD CELLS: ROGUELITE RPG</b> 🩸\n\n"
        f"Hujayralar yig'ing, o'ling va kuchliroq bo'lib qayta tiriling!\n\n"
        f"👤 Sinfingiz: <b>{cls_info['name']}</b>\n"
        f"❤️ Salomatlik: <b>{user['hp']}/{user['max_hp']}</b>\n"
        f"🧪 Zelyelar: <b>{user['potions']} ta</b>\n"
        f"🧬 Hujayralar (Cells): <b>{user['cells']}</b>\n\n"
        f"Jangni boshlash uchun /fight bosing!\n"
        f"Doimiy kuchayish uchun /shop bosing!"
    )

@dp.message(Command("fight"))
async def fight_cmd(message: types.Message):
    user = get_user(message.from_user.id)
    
    if user["hp"] <= 0:
        user["hp"] = user["max_hp"]
        
    enemy_template = random.choice(ENEMIES)
    user["enemy"] = {
        "name": enemy_template["name"],
        "hp": enemy_template["hp"],
        "max_hp": enemy_template["hp"],
        "damage": enemy_template["damage"],
        "cells": enemy_template["cells"]
    }
    user["in_battle"] = True
    save_data(user_data)

    cls_info = CLASSES[user["cls"]]
    await message.answer(
        f"👾 <b>DUSHMAN PAYDO BO'LDI!</b>\n\n"
        f"Dushman: <b>{user['enemy']['name']}</b> (HP: {user['enemy']['hp']}/{user['enemy']['max_hp']})\n"
        f"Siz: <b>{cls_info['name']}</b> (HP: {user['hp']}/{user['max_hp']})\n\n"
        f"Harakatni tanlang:",
        reply_markup=get_battle_keyboard(user),
        parse_mode="HTML"
    )

@dp.callback_query(F.data.startswith("act_"))
async def process_action(callback: types.CallbackQuery):
    user = get_user(callback.from_user.id)
    action = callback.data
    
    if not user.get("in_battle") or not user.get("enemy"):
        await callback.answer("Hozir jangda emassiz! /fight bosing.", show_alert=True)
        return

    enemy = user["enemy"]
    cls_info = CLASSES[user["cls"]]
    log_text = ""

    if action == "act_swap":
        await callback.message.edit_text(
            "🔄 Qaysi sinfga o'tishni xohlaysiz?",
            reply_markup=get_swap_keyboard(user)
        )
        return

    if action == "act_heal":
        if user["potions"] > 0:
            user["potions"] -= 1
            heal_amount = 45
            user["hp"] = min(user["max_hp"], user["hp"] + heal_amount)
            log_text += f"🧪 Zelye ichdingiz! +<b>{heal_amount}</b> HP qaytdi.\n"
        else:
            await callback.answer("❌ Zelye qolmagan!", show_alert=True)
            return

    elif action == "act_attack":
        dmg = random.randint(*cls_info["damage"])
        enemy["hp"] -= dmg
        log_text += f"⚔️ Siz {cls_info['name']} bilan <b>{dmg}</b> zarar yetkazdingiz!\n"

    elif action == "act_skill":
        dmg = random.randint(*cls_info["skill_dmg"])
        enemy["hp"] -= dmg
        log_text += f"⚡ <b>{cls_info['skill']}!</b> <b>{dmg}</b> zarar yetkazildi!\n"

    # Dushman mag'lub bo'ldimi?
    if enemy["hp"] <= 0:
        earned_cells = enemy["cells"]
        user["cells"] += earned_cells
        user["in_battle"] = False
        user["enemy"] = None
        
        # Tasodifiy yangi sinf/kalla ochilishi
        drop_msg = ""
        locked = [k for k in CLASSES.keys() if k not in user["unlocked"]]
        if locked and random.random() < 0.35:
            new_cls = random.choice(locked)
            user["unlocked"].append(new_cls)
            drop_msg = f"\n🎁 <b>YANGI SINF OCHILDI:</b> {CLASSES[new_cls]['name']}!"

        save_data(user_data)
        await callback.message.edit_text(
            f"🏆 <b>G'ALABA!</b>\n\n"
            f"Siz {enemy['name']}ni tor-mor etdingiz!\n"
            f"🧬 Yutdingiz: +<b>{earned_cells}</b> Hujayra (Cells)!{drop_msg}\n\n"
            f"Yangi jang uchun /fight bosing!"
        )
        return

    # Dushman hujumi
    e_dmg = random.randint(*enemy["damage"])
    user["hp"] -= e_dmg
    log_text += f"💥 {enemy['name']} sizga <b>{e_dmg}</b> zarar yetkazdi!\n"

    # O'lim holati (Roguelite Rebirth)
    if user["hp"] <= 0:
        user["hp"] = 0
        user["in_battle"] = False
        user["enemy"] = None
        save_data(user_data)
        
        await callback.message.edit_text(
            f"☠️ <b>SIZ O'LDINGIZ!</b>\n\n"
            f"Lekin Hujayralaringiz (<b>{user['cells']} Cells</b>) saqlanib qoldi.\n"
            f"Laboratoriyada qayta tirilish va jangni davom ettirish uchun /fight bosing!"
        )
        return

    save_data(user_data)
    await callback.message.edit_text(
        f"🩸 <b>JANG KETMOQDA</b>\n\n"
        f"{log_text}\n"
        f"Dushman HP: <b>{max(0, enemy['hp'])}/{enemy['max_hp']}</b>\n"
        f"Sizning HP: <b>{user['hp']}/{user['max_hp']}</b>\n\n"
        f"Keyingi harakat:",
        reply_markup=get_battle_keyboard(user)
    )

@dp.callback_query(F.data.startswith("set_cls_"))
async def set_cls_handler(callback: types.CallbackQuery):
    user = get_user(callback.from_user.id)
    c_key = callback.data.split("set_cls_")[1]
    
    if c_key in user["unlocked"]:
        user["cls"] = c_key
        save_data(user_data)
        await callback.answer(f"Sinf almashtirildi: {CLASSES[c_key]['name']}")
        
        if user.get("in_battle") and user.get("enemy"):
            enemy = user["enemy"]
            await callback.message.edit_text(
                f"🔄 Sinf o'zgardi: <b>{CLASSES[c_key]['name']}</b>\n\n"
                f"Dushman: <b>{enemy['name']}</b> (HP: {enemy['hp']}/{enemy['max_hp']})\n"
                f"Sizning HP: <b>{user['hp']}/{user['max_hp']}</b>\n\n"
                f"Harakatni tanlang:",
                reply_markup=get_battle_keyboard(user)
            )
        else:
            await callback.message.edit_text(f"Hozirgi sinf: {CLASSES[c_key]['name']}\n\nJang uchun /fight bosing!")

@dp.message(Command("shop"))
async def shop_cmd(message: types.Message):
    user = get_user(message.from_user.id)
    await message.answer(
        f"🧬 <b>LABORATORIYA (SHOP)</b> 🧬\n\n"
        f"Sizda: <b>{user['cells']} Cells</b>\n"
        f"Maksimal HP: <b>{user['max_hp']}</b>\n\n"
        f"1. Max HP oshirish (+20 HP) - <b>50 Cells</b>\n"
        f"2. Zelye sotib olish (+1 Potions) - <b>30 Cells</b>\n\n"
        f"Sotib olish uchun buyruqlar:\n"
        f"/buy_hp\n"
        f"/buy_potion"
    )

@dp.message(Command("buy_hp"))
async def buy_hp(message: types.Message):
    user = get_user(message.from_user.id)
    if user["cells"] >= 50:
        user["cells"] -= 50
        user["max_hp"] += 20
        user["hp"] += 20
        save_data(user_data)
        await message.answer(f"🎉 Maksimal HP oshirildi! Yangi HP: <b>{user['max_hp']}</b>")
    else:
        await message.answer("❌ Hujayralar (Cells) yetarli emas!")

@dp.message(Command("buy_potion"))
async def buy_potion(message: types.Message):
    user = get_user(message.from_user.id)
    if user["cells"] >= 30:
        user["cells"] -= 30
        user["potions"] += 1
        save_data(user_data)
        await message.answer(f"🧪 Yangi zelye olindi! Jami: <b>{user['potions']} ta</b>")
    else:
        await message.answer("❌ Hujayralar (Cells) yetarli emas!")

async def main():
    logger.info("Dead Cells Game Bot ishga tushmoqda...")

    # Render porti uchun mini web-server
    async def handle(request):
        return web.Response(text="Dead Cells RPG Bot is running!")

    app = web.Application()
    app.router.add_get('/', handle)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 8080))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()

    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot to'xtatildi.")
