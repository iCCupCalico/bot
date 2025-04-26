from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
import datetime
import json

TOKEN = '8126874985:AAFDkWiiUOmG5jKOViBtjs-4BiC0CpBqprM'
ADMIN_CHAT_ID = -1002699790388  # ID административного канала (начинается с "-100" для каналов)

# Словарь для хранения тикетов в памяти (можно заменить на базу или файл)
tickets = {}


async def start_tech_support(message):
    await message.answer("Здравствуйте! Вы обратились в техподдержку. Чем можем помочь?")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    text = update.message.text
    time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Проверяем, есть ли открытые тикеты у пользователя
    for ticket_id, ticket in tickets.items():
        if ticket['user_id'] == user.id and not ticket.get('closed'):
            # Добавляем уточнение в существующий тикет
            ticket['updates'].append({'time': time, 'message': text})
            with open('tickets.json', 'w', encoding='utf-8') as f:
                json.dump(tickets, f, ensure_ascii=False, indent=2)

            await update.message.reply_text(f"Ваше уточнение добавлено в тикет №{ticket_id}.")
            await context.bot.send_message(
                chat_id=ADMIN_CHAT_ID,
                text=f"Обновление тикета №{ticket_id} от {user.full_name} (@{user.username}):\n{text}"
            )
            return

    # Если открытых тикетов нет, создаём новый
    ticket_id = int(datetime.datetime.now().timestamp())

    ticket_info = {
        'user_id': user.id,
        'username': user.username,
        'full_name': user.full_name,
        'time': time,
        'problem': text,
        'updates': [],
        'closed': False
    }

    tickets[ticket_id] = ticket_info

    # Сохраняем тикеты в файл
    with open('tickets.json', 'w', encoding='utf-8') as f:
        json.dump(tickets, f, ensure_ascii=False, indent=2)

    ticket_text = (
        f"[{ticket_id}] {time}\n"
        f"От: {user.full_name} (@{user.username})\n"
        f"Проблема: {text}\n\n"
    )

    # Отправляем админу
    await context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=f"Новый тикет!\n{ticket_text}")

    # Подтверждение пользователю
    await update.message.reply_text(f"Спасибо! Ваш тикет №{ticket_id} принят. Ожидайте ответа.")


async def reply_to_ticket(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.text.startswith('/reply'):
        return

    try:
        command_parts = update.message.text.split(maxsplit=2)
        ticket_id = int(command_parts[1])
        reply_text = command_parts[2]
    except (IndexError, ValueError):
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Используйте команду так: /reply <ticket_id> <текст ответа>")
        return

    # Загружаем тикеты из файла
    global tickets
    try:
        with open('tickets.json', 'r', encoding='utf-8') as f:
            tickets = json.load(f)
    except FileNotFoundError:
        tickets = {}

    ticket = tickets.get(str(ticket_id))
    if not ticket:
        await context.bot.send_message(chat_id=update.effective_chat.id, text=f"Тикет с ID {ticket_id} не найден.")
        return

    user_id = ticket['user_id']

    # Отправляем ответ пользователю
    await context.bot.send_message(chat_id=user_id, text=f"Ответ на ваш тикет №{ticket_id}:\n{reply_text}")
    await context.bot.send_message(chat_id=update.effective_chat.id, text=f"Ответ на тикет №{ticket_id} успешно отправлен пользователю.")


async def close_ticket(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.text.startswith('/close'):
        return

    try:
        command_parts = update.message.text.split(maxsplit=1)
        ticket_id = int(command_parts[1])
    except (IndexError, ValueError):
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Используйте команду так: /close <ticket_id>")
        return

    # Загружаем тикеты из файла
    global tickets
    try:
        with open('tickets.json', 'r', encoding='utf-8') as f:
            tickets = json.load(f)
    except FileNotFoundError:
        tickets = {}

    ticket = tickets.get(str(ticket_id))
    if not ticket:
        await context.bot.send_message(chat_id=update.effective_chat.id, text=f"Тикет с ID {ticket_id} не найден.")
        return

    if ticket.get('closed'):
        await context.bot.send_message(chat_id=update.effective_chat.id, text=f"Тикет №{ticket_id} уже закрыт.")
        return

    ticket['closed'] = True

    # Сохраняем изменения в файл
    with open('tickets.json', 'w', encoding='utf-8') as f:
        json.dump(tickets, f, ensure_ascii=False, indent=2)

    user_id = ticket['user_id']
    await context.bot.send_message(chat_id=user_id, text=f"Ваш тикет №{ticket_id} был закрыт.")
    await context.bot.send_message(chat_id=update.effective_chat.id, text=f"Тикет №{ticket_id} успешно закрыт.")


def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler('start', start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(MessageHandler(filters.TEXT & filters.ChatType.GROUPS, reply_to_ticket))  # Ответ через канал
    app.add_handler(MessageHandler(filters.TEXT & filters.ChatType.GROUPS, close_ticket))  # Закрытие через канал

    app.run_polling()


if __name__ == '__main__':
    main()