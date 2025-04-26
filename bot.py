import logging
from typing import Dict, Optional
import telebot
from telebot.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton

from scraper import get_player_stats

# Глобальные переменные для хранения состояния бота
user_states = {}  # {user_id: {state: str, data: {}}}
STATE_WAITING_FOR_NICKNAME = 'waiting_for_nickname'
STATE_WAITING_FOR_SUPPORT_MESSAGE = 'waiting_for_support_message'



def format_stats_message(nickname: str, stats: Dict) -> str:
    """Format player stats into a readable message."""
    # Базовое форматирование сообщения
    display_name = stats.get('username', nickname)
    message = f"<b>Статистика игрока {display_name} .:</b>\n\n"

    # Проверяем статус игрока
    if stats.get('status') == "Нет игр":
        message += f"😢 <b>Игрок еще не сыграл ни одной игры</b>\n"
        message += f"\n<i>Данные получены с сайта iccup.com</i>"
        return message

    # Основные показатели

    if stats.get('pts'):
        message += f" :</b> {stats['pts']}\n"

    if stats.get('rank'):
        message += f" <code> Ранг </code> {stats['rank']}\n"

    # Статистика игр
    if stats.get('games_played'):
        message += f" <code>Всего игр:</code> {stats['games_played']}\n"

        if stats.get('win_ratio') is not None:
            message += f"📊 <b>Процент побед:</b> {stats['win_ratio']}%\n"

    # Отдельно выводим W/L если доступно
    if stats.get('wins') is not None and stats.get('losses') is not None:
        message += f"✅ <b>Победы/Поражения:</b> {stats['wins']} / {stats['losses']}\n"

    # KDA статистика, если доступна
    if stats.get('average_kills') is not None:
        message += f"⚔️ <b>Среднее K/D/A:</b> {stats.get('average_kills', 0)}/{stats.get('average_deaths', 0)}/{stats.get('average_assists', 0)}\n"

    # Локация и другая информация
    if stats.get('location'):
        message += f"🌍 <b>Локация:</b> {stats['location']}\n"

    # Дополнительные статистические данные
    additional_keys = [
        'apm', 'farm', 'experience_per_min', 'gank_participation',
        'total_match_time', 'avg_match_time', 'leave_rate'
    ]

    # Словарь для красивых названий
    nice_names = {
        'apm': 'APM',
        'farm': 'Фарм',
        'experience_per_min': 'Опыт в минуту',
        'gank_participation': 'Участие в ганках',
        'total_match_time': 'Общее время матчей',
        'avg_match_time': 'Среднее время матча',
        'leave_rate': 'Процент выходов'
    }

    # Выводим дополнительную статистику
    for key in additional_keys:
        if stats.get(key) is not None:
            display_name = nice_names.get(key, key.replace('_', ' ').title())

            # Форматируем значение, если это процент
            if isinstance(stats[key], (float, int)) and 'rate' in key:
                message += f"📊 <b>{display_name}:</b> {stats[key]}%\n"
            else:
                message += f"📊 <b>{display_name}:</b> {stats[key]}\n"

    # Добавляем остальные статистические данные, которые мы не обработали
    excluded_keys = ['username', 'pts', 'rank', 'games_played', 'win_ratio', 'wins', 'losses',
                     'average_kills', 'average_deaths', 'average_assists', 'location', 'status'] + additional_keys

    for key, value in stats.items():
        if key not in excluded_keys:
            # Формируем человекочитаемое название поля
            display_name = key.replace('_', ' ').title()
            message += f"ℹ️ <b>{display_name}:</b> {value}\n"

    return message


def setup_bot(token: str) -> telebot.TeleBot:
    """Setup and return the bot instance."""
    bot = telebot.TeleBot(token, parse_mode='HTML')

    # Функция для создания главного меню
    def get_main_menu():
        markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
        stats_btn = KeyboardButton('📊 Статистика')
        contests_btn = KeyboardButton('🏆 Конкурсы')
        FAQ_btn = KeyboardButton('🏆 F.A.Q')
        Tech_btn = KeyboardButton('Техническая поддержка')
        markup.add(stats_btn, contests_btn, FAQ_btn, Tech_btn)
        return markup

    # Обработчик команды /start
    @bot.message_handler(commands=['start'])
    def start_command(message: Message):
        """Sends a welcome message when the command /start is issued."""
        bot.send_message(
            message.chat.id,
            f'Привет, {message.from_user.first_name}! 👋\n\n'
            'Я бот для получения статистики игроков DotA с сайта iccup.com. '
            'С моей помощью вы можете быстро узнать рейтинг и достижения любого игрока!\n\n'
            'Что я умею:\n'
            '• Получать статистику игроков по никнейму\n'
            '• Предоставлять полезную информацию об игре\n'
            '• Сообщать о новых конкурсах и событиях\n\n'
            'Используйте кнопки меню или команду /stats для начала работы.',
            reply_markup=get_main_menu()
        )

    # Обработчик команды /menu
    @bot.message_handler(commands=['menu'])
    def menu_command(message: Message):
        """Показывает главное меню"""
        bot.send_message(
            message.chat.id,
            'Главное меню:',
            reply_markup=get_main_menu()
        )

    # Обработчик инлайн-кнопок
    @bot.callback_query_handler(func=lambda call: True)
    def handle_callback_query(call):
        """Обрабатывает нажатия на инлайн-кнопки"""
        # Извлекаем данные колбэка
        callback_data = call.data

        # Обработка информационных запросов
        if callback_data.startswith('info_'):
            # Получаем ключ для информации
            info_key = callback_data.split('_')[1]
            if info_key in INFO_DATABASE:
                bot.answer_callback_query(call.id)
                bot.send_message(call.message.chat.id, INFO_DATABASE[info_key])
            else:
                bot.answer_callback_query(call.id, "Информация не найдена", show_alert=True)

        # Возврат в главное меню
        elif callback_data == 'back_to_main':
            bot.answer_callback_query(call.id)
            bot.delete_message(call.message.chat.id, call.message.message_id)
            bot.send_message(call.message.chat.id, "Главное меню:", reply_markup=get_main_menu())

    # Обработчик команды /stats
    @bot.message_handler(commands=['stats'])
    def stats_command(message: Message):
        """Process the /stats command."""
        # Проверяем, есть ли параметр после команды
        command_parts = message.text.split()

        if len(command_parts) > 1:
            # Если есть параметр после команды, используем его как никнейм
            nickname = command_parts[1].strip()
            process_stats_request(message, nickname)
        else:
            # Если параметра нет, просим пользователя ввести никнейм
            msg = bot.send_message(
                message.chat.id,
                'Пожалуйста, введите никнейм игрока:'
            )
            # Устанавливаем состояние ожидания никнейма
            user_states[message.from_user.id] = {'state': STATE_WAITING_FOR_NICKNAME}
            # Регистрируем следующий шаг
            bot.register_next_step_handler(msg, process_nickname_input)

    # Обработчик ввода никнейма после команды /stats
    def process_nickname_input(message: Message):
        """Process nickname input after /stats command."""
        # Проверяем, что пользователь находится в нужном состоянии
        user_id = message.from_user.id

        if user_id in user_states and user_states[user_id]['state'] == STATE_WAITING_FOR_NICKNAME:
            # Получаем никнейм из сообщения
            nickname = message.text.strip()

            # Сбрасываем состояние пользователя
            user_states.pop(user_id, None)

            # Обрабатываем запрос статистики
            process_stats_request(message, nickname)
        else:
            # Если пользователь не в режиме ожидания никнейма, игнорируем сообщение
            pass


    # Функция обработки запроса статистики
    def process_stats_request(message: Message, nickname: str):
        """Process a statistics request for a given nickname."""
        # Логируем запрос
        logging.info(f"User {message.from_user.id} requested stats for '{nickname}'")

        # Показываем "печатает..." пока обрабатываем запрос
        bot.send_chat_action(message.chat.id, 'typing')

        try:
            # Получаем статистику игрока
            stats = get_player_stats(nickname)

            if stats:
                # Форматируем сообщение
                formatted_message = format_stats_message(nickname, stats)
                bot.send_message(message.chat.id, formatted_message)
            else:
                bot.send_message(
                    message.chat.id,
                    f'Не удалось найти игрока с никнеймом "{nickname}". '
                    f'Проверьте правильность написания и попробуйте снова.\n'
                    f'Используйте команду /stats для нового поиска.',
                    reply_markup=get_main_menu()
                )
        except Exception as e:
            logging.error(f"Error processing stats for {nickname}: {str(e)}")
            bot.send_message(
                message.chat.id,
                'Произошла ошибка при получении статистики. Пожалуйста, попробуйте позже.\n'
                'Используйте команду /stats для нового поиска.',
                reply_markup=get_main_menu()
            )

    # Обработчик команды /cancel
    @bot.message_handler(commands=['cancel'])
    def cancel_command(message: Message):
        """Cancel the current operation."""
        user_id = message.from_user.id

        # Сбрасываем состояние пользователя
        if user_id in user_states:
            user_states.pop(user_id, None)

        bot.send_message(
            message.chat.id,
            'Операция отменена. Вы в главном меню.',
            reply_markup=get_main_menu()
        )

    # Обработчик текстовых сообщений (для обработки кнопок меню и других сообщений)
    @bot.message_handler(func=lambda message: True, content_types=['text'])
    def text_message_handler(message: Message):
        """Обрабатывает текстовые сообщения и нажатия на кнопки меню"""
        # Проверяем состояние пользователя
        user_id = message.from_user.id
        text = message.text.strip()

        # Если пользователь в состоянии ожидания ввода
        if user_id in user_states:
            state = user_states[user_id]['state']

            if state == STATE_WAITING_FOR_NICKNAME:
                # Если ожидается никнейм
                process_nickname_input(message)
                return

            elif state == STATE_WAITING_FOR_SUPPORT_MESSAGE:
                # Если ожидается сообщение для техподдержки
                process_support_message(message)
                return

        # Обработка нажатий на кнопки меню
        if text.startswith('📊 Статистика'):
            # Запрашиваем ввод никнейма для получения статистики
            msg = bot.send_message(
                message.chat.id,
                'Пожалуйста, введите никнейм игрока:'
            )
            # Устанавливаем состояние ожидания никнейма
            user_states[user_id] = {'state': STATE_WAITING_FOR_NICKNAME}
            # Регистрируем следующий шаг
            bot.register_next_step_handler(msg, process_nickname_input)


        elif text.startswith('🏆 Конкурсы'):
            # Отправляем информацию о конкурсах
            contest_message = (
                "🎭 <b>Актуальный конкурс: <a href='https://t.me/iCCup/6839'>Пародист</a></b>"

            )
            bot.send_message(message.chat.id, contest_message)

        elif text.startswith('🏆 F.A.Q'):
            # Отправляем информацию о FAQ
            faq_message = (
                "здесь будет FAQ"

            )
            bot.send_message(message.chat.id, faq_message)

        elif text.startswith('Техническая поддержка'):
            # Tech supp
            Tech_message = (
                "1. <a href='https://t.me/iCCupTech/2'>Существуют ли версии лаунчера для Mac OS и unix?т</a> .\n"
                "2. <a href='https://t.me/iCCupTech/3'> Could not connect to Battle.Net/Не удалось установить соединение</a>.\n"

            )
            bot.send_message(message.chat.id, Tech_message)

        else:
            # Если не распознали команду - показываем подсказку
            bot.send_message(
                message.chat.id,
                'Для взаимодействия с ботом используйте кнопки меню или следующие команды:\n'
                '/start - главное меню\n'
                '/menu - показать меню\n'
                '/stats - получить статистику игрока\n'
                '/cancel - отменить текущую операцию',
                reply_markup=get_main_menu()
            )

    return bot
