import os
import telebot

TOKEN = os.environ["BOT_TOKEN"]

bot = telebot.TeleBot(TOKEN)

# ...your other bot commands here...

print("🟢 BOT STARTED")

bot.infinity_polling(
    timeout=60,
    long_polling_timeout=60
)
