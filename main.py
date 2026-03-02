import asyncio
import sys
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pytgcalls import PyTgCalls
from pytgcalls.types.input_stream import InputAudioStream
from yt_dlp import YoutubeDL

from config import *
from logger import logger

bot = Client("UltraMusicBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
call_py = PyTgCalls(bot)

QUEUE = {}
CURRENT = {}
PLAY_COUNT = {}

# ================= SAFE RUNNER (ANTI CRASH) ================= #

async def safe_run():
    while True:
        try:
            await bot.start()
            await call_py.start()
            logger.info("Bot Started Successfully")
            await bot.idle()
        except Exception as e:
            logger.error(f"Crash Detected: {e}")
            await asyncio.sleep(5)

# ================= START ================= #

@bot.on_message(filters.command("start") & filters.private)
async def start(_, message):
    msg = await message.reply_text("Bot starting.")
    await asyncio.sleep(1)
    await msg.edit("Bot starting..")
    await asyncio.sleep(1)
    await msg.edit("Bot starting...")

    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("ᴀᴅᴅ ᴍᴇ ɪɴ ʏᴏᴜʀ ɢʀᴏᴜᴘ",
         url=f"https://t.me/{(await bot.get_me()).username}?startgroup=true")],
        [InlineKeyboardButton("● Pʀᴏᴍᴏᴛɪᴏɴ", callback_data="promo")],
        [InlineKeyboardButton("sᴜᴘᴘᴏʀᴛ", url=SUPPORT_LINK)],
        [InlineKeyboardButton("ᴅᴇᴠᴇʟᴏᴘᴇʀ", url=f"https://t.me/{OWNER_USERNAME}")]
    ])

    await msg.edit("🎵 𝐔𝐋𝐓𝐑𝐀 𝐏𝐑𝐎 𝐌𝐔𝐒𝐈𝐂 𝐁𝐎𝐓", reply_markup=buttons)

# ================= PROMOTION ================= #

@bot.on_callback_query(filters.regex("promo"))
async def promo(_, cb):

    text = """─────────────────────────
❖ ᴘᴧɪᴅ ᴘʀσϻσᴛɪση ᴧᴠᴧɪʟᴧʙʟє ❖
─────────────────────────
❍ ᴄʜᴧᴛᴛɪηɢ ɢʀσυᴘ's
❍ ᴄσʟσʀ ᴛʀᴧᴅɪηɢ ɢᴧϻє's
❍ ᴄʜᴧηηєʟ's | ɢʀσυᴘ's
❍ ʙєᴛᴛɪηɢ ᴧᴅs σʀ ᴧηʏᴛʜɪηɢ
─────────────────────────
● ᴅᴧɪʟʏ . ᴡєєᴋʟʏ . ᴧηᴅ ϻσηᴛʜʟʏ ᴘʟᴧη'ꜱ
─────────────────────────
❍ ᴄσηᴛᴧᴄᴛ - @lx_maxx
─────────────────────────"""

    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("ᴅᴇᴠ", url=f"https://t.me/{OWNER_USERNAME}")],
        [InlineKeyboardButton("- ʙᴀᴄᴋ ᴛᴏ ʜᴏᴍᴇ -", callback_data="home")]
    ])

    await cb.message.edit(text, reply_markup=buttons)

# ================= PLAY ================= #

@bot.on_message(filters.command("play") & filters.group)
async def play(_, message):

    if len(message.command) < 2:
        return await message.reply_text("❌ Give Song Name")

    query = " ".join(message.command[1:])
    processing = await message.reply_text("🥀 𝐏ɤσƈɛssɩŋʛ... 🦋")

    try:
        with YoutubeDL({'format': 'bestaudio', 'quiet': True}) as ydl:
            info = ydl.extract_info(f"ytsearch:{query}", download=False)['entries'][0]
    except:
        return await processing.edit("❌ Song Not Found")

    title = info['title']
    duration = info['duration']
    thumb = info['thumbnail']
    url = info['url']

    chat_id = message.chat.id

    if chat_id not in QUEUE:
        QUEUE[chat_id] = []
        PLAY_COUNT[chat_id] = 0

    QUEUE[chat_id].append((title, url, duration, message.from_user.first_name, thumb))

    await processing.delete()
    await message.reply_text(f"➕ Added To Queue: {title}")

    if chat_id not in CURRENT:
        await start_stream(chat_id)

# ================= STREAM ================= #

async def start_stream(chat_id):

    if not QUEUE.get(chat_id):
        await call_py.leave_group_call(chat_id)
        CURRENT.pop(chat_id, None)
        return

    title, url, duration, user, thumb = QUEUE[chat_id].pop(0)
    CURRENT[chat_id] = title
    PLAY_COUNT[chat_id] += 1

    await call_py.join_group_call(chat_id, InputAudioStream(url))

    minutes = duration // 60
    seconds = duration % 60

    caption = f"""❖ 𝛅ᴛᴧʀᴛєᴅ 𝛅ᴛʀєᴧϻɪηɢ
❍ тɪᴛʟє : {title}
❍ ᴅᴜʀᴧᴛɪση : {minutes}:{seconds}
❍ ʙʏ : {user}"""

    buttons = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("⏭ Skip", callback_data="skip"),
            InlineKeyboardButton("⏹ Stop", callback_data="stop")
        ],
        [
            InlineKeyboardButton("❌ Close", callback_data="close")
        ]
    ])

    await bot.send_photo(chat_id, thumb, caption=caption, reply_markup=buttons)

    # ================= ADS SYSTEM ================= #
    if PLAY_COUNT[chat_id] % AD_INTERVAL == 0:
        await bot.send_message(chat_id, AD_MESSAGE)

# ================= CONTROLS ================= #

@bot.on_callback_query(filters.regex("skip"))
async def skip(_, cb):
    await start_stream(cb.message.chat.id)

@bot.on_callback_query(filters.regex("stop"))
async def stop(_, cb):
    QUEUE[cb.message.chat.id] = []
    await call_py.leave_group_call(cb.message.chat.id)

@bot.on_callback_query(filters.regex("close"))
async def close(_, cb):
    user = cb.from_user.first_name
    await cb.message.delete()
    await cb.message.reply_text(f"ᴄʟᴏsᴇ ʙʏ :- {user}")

@call_py.on_stream_end()
async def on_end(_, update):
    await start_stream(update.chat_id)

# ================= MAIN ================= #

if __name__ == "__main__":
    asyncio.run(safe_run())
