import os
import logging
import time
from logger import setup_logger
from bot import setup_bot


def start_telegram_bot():
    # Initialize logger
    logger = setup_logger()

    # Retrieve API token
    token = ("7611836265:AAEtc9lllZ2RfOrKLdYUKGZwwkan9syGvD8")
    if not token:
        logger.error('TELEGRAM_BOT_TOKEN not set!')
        return

    logger.info('Starting bot with provided token')
    bot = setup_bot(token)
    bot.enable_save_next_step_handlers(delay=2)

    try:
        logger.info('Polling started')
        bot.polling(none_stop=True, interval=0, timeout=20)
    except KeyboardInterrupt:
        logger.info('Polling stopped by user')
    except Exception as err:
        logger.exception('Polling error: %s', err)
    finally:
        bot.stop_polling()
        logger.info('Polling fully stopped')


if __name__ == '__main__':
    start_telegram_bot()
