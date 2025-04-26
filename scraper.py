import logging
import requests
from bs4 import BeautifulSoup
from typing import Dict, Optional

# Set up logger
logger = logging.getLogger(__name__)


def get_player_stats(nickname: str) -> Optional[Dict]:
    """
    Scrape player statistics from iccup.com DotA profile page.

    Args:
        nickname: The player's nickname/username on iccup.com

    Returns:
        Dictionary containing player statistics or None if player not found
    """
    url = f"https://iccup.com/dota/gamingprofile/{nickname}.html"
    # Fix URL if running in localhost - add the protocol and domain explicitly
    if url.startswith('/'):
        url = 'https://iccup.com' + url

    try:
        # Log the scraping attempt
        logger.info(f"Scraping stats for player '{nickname}' from {url}")

        # Send the HTTP request
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)

        # Check if the request was successful
        if response.status_code != 200:
            logger.warning(f"Failed to retrieve page for {nickname}. Status code: {response.status_code}")
            return None

        # Parse the HTML content
        soup = BeautifulSoup(response.text, 'html.parser')

        # Check if profile exists
        if "Player not found" in response.text or "Profile not found" in response.text:
            logger.warning(f"Player '{nickname}' not found on iccup.com")
            return None

        # Extract player statistics
        stats = extract_player_stats(soup)

        if not stats:
            logger.warning(f"Could not extract stats for player '{nickname}'")
            return None

        logger.info(f"Successfully scraped stats for '{nickname}'")
        return stats

    except requests.exceptions.RequestException as e:
        logger.error(f"Request error when scraping stats for '{nickname}': {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Error scraping stats for '{nickname}': {str(e)}")
        return None


def extract_player_stats(soup: BeautifulSoup) -> Dict:
    """
    Extract player statistics from the BeautifulSoup parsed HTML.

    Args:
        soup: BeautifulSoup object of the player's profile page

    Returns:
        Dictionary containing parsed player statistics
    """
    stats = {}

    try:
        # Получаем имя игрока
        username_element = soup.select_one('.profile-uname')
        if username_element:
            stats['username'] = username_element.text.strip()

        # Извлекаем статистику из таблиц
        stat_tables = soup.select('table.stata-body')

        for table in stat_tables:
            rows = table.select('tr')
            for row in rows:
                cells = row.select('td')
                if len(cells) >= 2:
                    key = cells[0].text.strip().lower().replace(' ', '_')
                    value_text = cells[1].text.strip()

                    # Попытка преобразовать в число, если это возможно
                    try:
                        # Удаляем знак % и другие символы
                        if '%' in value_text:
                            value = float(value_text.replace('%', ''))
                        elif value_text.replace('.', '', 1).isdigit():
                            if '.' in value_text:
                                value = float(value_text)
                            else:
                                value = int(value_text)
                        else:
                            value = value_text
                        stats[key] = value
                    except ValueError:
                        stats[key] = value_text

        # Получаем данные о рейтинге
        rating_table = soup.select_one('table.t-table')
        if rating_table:
            rating_rows = rating_table.select('tr')
            # Пропускаем заголовок таблицы
            for i, row in enumerate(rating_rows):
                if i > 0:  # Пропускаем заголовок
                    cells = row.select('td')
                    if len(cells) >= 4:
                        # В таблице обычно есть PTS и Rank
                        stats['pts'] = cells[2].text.strip() if len(cells) > 2 else "0"

                        # Также можем извлечь позицию в рейтинге
                        stats['rank'] = cells[0].text.strip() if cells[0].text.strip() != "#" else "Не в рейтинге"
                    break  # Берем только первую строку с данными

        # Извлекаем статистику W/L, если она есть
        if 'win_ratio' in stats:
            # Если у нас есть процент побед, попробуем вычислить W/L
            if 'games_played' in stats:
                games = stats['games_played']
                win_ratio = stats['win_ratio'] / 100  # Convert percentage to decimal
                stats['wins'] = int(games * win_ratio)
                stats['losses'] = games - stats['wins']

        # Проверяем, есть ли хоть какая-то статистика
        if not stats or len(stats) <= 1:  # Если только имя пользователя
            # Пробуем найти сообщение о том, что игрок не играл
            not_played_msg = None
            for element in soup.find_all(string=True):
                if "hasn't played" in element.lower():
                    not_played_msg = element
                    break

            if not_played_msg:
                logger.warning(f"Player hasn't played any games yet.")
                stats['status'] = "Нет игр"
            else:
                # Если мы здесь, значит что-то пошло не так
                logger.warning("Could not find any stats in the expected format")

        return stats

    except Exception as e:
        logger.error(f"Error extracting stats from HTML: {str(e)}")
        return {}
