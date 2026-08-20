import logging
import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.utils.keyboard import InlineKeyboardBuilder

# Loglarni sozlash (Render loglarida ko'rinishi uchun)
logging.basicConfig(level=logging.INFO)

# O'z API Tokeningizni kiriting
BOT_TOKEN = "8916790366:AAErADCcTeCSXydXrAt5VSIH99k_yXJecm8"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# O'yin holatini saqlash uchun vaqtinchalik xotira
games = {}

# 3x3 o'yin taxtasini yaratish funksiyasi
def create_board_keyboard(board):
    builder = InlineKeyboardBuilder()
    for i in range(9):
        display_text = "⬜️" if board[i] == "" else board[i]
        builder.button(text=display_text, callback_data=f"xo_{i}")
    builder.adjust(3)  # 3x3 ko'rinishga keltirish
    return builder.as_markup()

# G'olibni aniqlash algoritmi
def check_winner(b):
    win_combinations = [
        (0,1,2), (3,4,5), (6,7,8), # Gorizontal
        (0,3,6), (1,4,7), (2,5,8), # Vertikal
        (0,4,8), (2,4,6)           # Diagonal
    ]
    for x, y, z in win_combinations:
        if b[x] != "" and b[x] == b[y] == b[z]:
            return b[x]
    if "" not in b:
        return "Durang"
    return None

# 1. Biznes chatda /game buyrug'i kelganda o'yinni boshlash
@dp.business_message(F.text.lower() == "/game")
async def start_game_business(message: types.Message):
    chat_id = message.chat.id
    bus_conn_id = message.business_connection_id 
    client_id = message.from_user.id
    
    # Yangi o'yin sessiyasini yaratish
    games[chat_id] = {
        "board": [""] * 9,
        "client": client_id,
        "turn": client_id,  # Birinchi bo'lib mijoz boshlaydi
        "bus_conn_id": bus_conn_id
    }
    
    kb = create_board_keyboard(games[chat_id]["board"])
    
    await message.answer(
        text="🎮 X/O O'yini boshlandi!\n\nNavbat: Mijozniki (⭕️)",
        reply_markup=kb,
        business_connection_id=bus_conn_id
    )

# 2. Telegram Business uchun Inline tugmalar bosilishini to'g'ri ushlash
@dp.callback_query(F.data.startswith("xo_"))
async def play_move(callback: types.CallbackQuery):
    chat_id = callback.message.chat.id
    user_id = callback.from_user.id
    
    # Agar ushbu chatda faol o'yin topilmasa
    if chat_id not in games:
        await callback.answer("O'yin topilmadi yoki yakunlangan.", show_alert=True)
        return

    game = games[chat_id]
    
    # Callback ma'lumotidan bosilgan katak indeksini ajratib olish (Xatolik to'g'rilandi)
    cell_index = int(callback.data.split("_")[1])
    
    # Navbatni tekshirish
    if user_id != game["turn"]:
        await callback.answer("Hozir sizning navbatingiz emas! ⏳", show_alert=True)
        return
        
    # Katak bo'shligini tekshirish
    if game["board"][cell_index] != "":
        await callback.answer("Bu katak allaqachon band! ❌", show_alert=True)
        return
        
    # Navbat va belgilarni yangilash
    if user_id == game["client"]:
        game["board"][cell_index] = "⭕️"
        game["turn"] = chat_id  # Navbat biznes egasiga o'tadi
        next_turn_text = "Biznes egasi (❌)"
    else:
        game["board"][cell_index] = "❌"
        game["turn"] = game["client"]  # Navbat mijozga o'tadi
        next_turn_text = "Mijoz (⭕️)"
        
    winner = check_winner(game["board"])
    kb = create_board_keyboard(game["board"])
    
    # O'yin natijasini tekshirish
    if winner:
        if winner == "Durang":
            text_result = "🤝 Durang! Yaxshi o'yin bo'ldi."
        elif winner == "⭕️":
            text_result = "🎉 Mijoz (⭕️) g'alaba qozondi! Sizga 10% chegirma kuponi: SALE10"
        else:
            text_result = "👑 Biznes egasi (❌) g'alaba qozondi!"
            
        await bot.edit_message_text(
            text=f"🎮 O'yin yakunlandi!\n\n{text_result}",
            chat_id=chat_id,
            message_id=callback.message.message_id,
            reply_markup=kb,
            business_connection_id=game["bus_conn_id"]
        )
        # O'yin tugagach xotiradan o'chirish
        del games[chat_id]
    else:
        # O'yinni davom ettirish va jonli yangilash
        await bot.edit_message_text(
            text=f"🎮 X/O O'yini davom etmoqda...\n\nNavbat: {next_turn_text}",
            chat_id=chat_id,
            message_id=callback.message.message_id,
            reply_markup=kb,
            business_connection_id=game["bus_conn_id"]
        )
        
    await callback.answer()

# Botni ishga tushirish funksiyasi
async def main():
    logging.info("Bot muvaffaqiyatli ishga tushirildi...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
