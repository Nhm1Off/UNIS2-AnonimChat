from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler, CallbackContext
import logging

# Ініціалізація бота
TOKEN = "7411990110:AAHctohfQCALjtkH3hG58snG1kaMNns09k4"
updater = Updater(token=TOKEN, use_context=True)
dispatcher = updater.dispatcher

# Налаштування логування
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Словник для зберігання даних користувачів
user_data = {}
chat_queue = {}

# Стани для розмови
GENDER, AGE, MENU = range(3)

# Функція старту
def start(update: Update, context: CallbackContext):
    keyboard = [["🔍 Знайти співрозмовника"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    update.message.reply_text(
        "Вітаю! Це анонімний чат. Щоб почати, введіть ваш гендер (чоловік/жінка):",
        reply_markup=reply_markup
    )

    return GENDER

# Збір гендеру
def set_gender(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    user_data[user_id] = {'gender': update.message.text}  # Зберігаємо гендер

    update.message.reply_text("Введіть ваш вік:")
    return AGE

# Збір віку
def set_age(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    user_data[user_id]['age'] = update.message.text  # Зберігаємо вік

    update.message.reply_text(
        f"Ваш гендер: {user_data[user_id]['gender']}, Ваш вік: {user_data[user_id]['age']}.\n"
        "Тепер ви готові до спілкування!",
        reply_markup=ReplyKeyboardMarkup([["🔍 Знайти співрозмовника"], ["❌ Завершити чат"]], resize_keyboard=True)
    )

    return MENU  # Переходить до меню

# Команда для пошуку співрозмовника
def find(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id

    if user_id not in chat_queue:
        chat_queue[user_id] = None
        update.message.reply_text("Шукаємо співрозмовника...")
        check_for_match(context)
    else:
        update.message.reply_text("Ви вже в черзі для пошуку.")

# Перевірка наявності пари для чату
def check_for_match(context: CallbackContext):
    if len(chat_queue) >= 2:
        users = list(chat_queue.keys())
        user1, user2 = users[0], users[1]

        user1_info = user_data[user1]
        user2_info = user_data[user2]

        context.bot.send_message(user1, f"Співрозмовника знайдено! Починайте спілкування.\nВаш гендер: {user1_info['gender']}, Ваш вік: {user1_info['age']}.")
        context.bot.send_message(user2, f"Співрозмовника знайдено! Починайте спілкування.\nВаш гендер: {user2_info['gender']}, Ваш вік: {user2_info['age']}.")

        # Встановлюємо пари
        chat_queue[user1] = user2
        chat_queue[user2] = user1

# Обробка повідомлень для пересилання між співрозмовниками
def message_handler(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    if user_id in chat_queue and chat_queue[user_id] is not None:
        partner_id = chat_queue[user_id]
        context.bot.send_message(partner_id, update.message.text)

# Функція завершення чату
def end_chat(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    if user_id in chat_queue:
        partner_id = chat_queue[user_id]
        context.bot.send_message(partner_id, "Ваш співрозмовник завершив чат.")
        context.bot.send_message(user_id, "Ви завершили чат.")
        del chat_queue[user_id]
        if partner_id:
            del chat_queue[partner_id]

        # Повернення до меню після завершення чату
        update.message.reply_text("Чат завершено. Ви можете шукати нового співрозмовника.",
                                  reply_markup=ReplyKeyboardMarkup([["🔍 Знайти співрозмовника"], ["❌ Завершити чат"]], resize_keyboard=True))

# Реєстрація хендлерів
conv_handler = ConversationHandler(
    entry_points=[CommandHandler("start", start)],
    states={
        GENDER: [MessageHandler(Filters.text, set_gender)],
        AGE: [MessageHandler(Filters.text, set_age)],
        MENU: [MessageHandler(Filters.regex("🔍 Знайти співрозмовника"), find),
               MessageHandler(Filters.regex("❌ Завершити чат"), end_chat)]
    },
    fallbacks=[]
)

dispatcher.add_handler(conv_handler)
dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, message_handler))

# Запуск бота
if __name__ == '__main__':
    updater.start_polling()
    updater.idle()
