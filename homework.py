import logging
import os
import sys
import time

import requests
import telegram
from http import HTTPStatus
from dotenv import load_dotenv
from typing import Dict, List, Union

import exceptions

load_dotenv()
PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
RETRY_PERIOD = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def check_tokens() -> bool:
    """Функция проверяет доступность переменных окружения.
    Если отсутствует хотя бы одна переменная окружения —
    происходит принудетельный выход из программы
    """
    return all((PRACTICUM_TOKEN, TELEGRAM_CHAT_ID, TELEGRAM_TOKEN))


def send_message(bot: telegram.Bot, message: str):
    """Функция отправляет сообщение в Telegram чат."""
    try:
        logging.info('Начинаем отправку сообщения!')
        bot.send_message(
            chat_id=TELEGRAM_CHAT_ID,
            text=message
        )
        logging.debug('Сообщение успешно отправлено в Telegram')
    except telegram.error.TelegramError:
        # Вроде все подправил, но с логами error проблемы.
        # Не пойму это тесты так требуют чтобы именно здесь
        # логи записывались об ошибке или я туплю.
        # Если убираю от сюда 'logging.error' то падают тесты.
        logging.error('Ошибка отправки сообщения в тг')
        raise exceptions.TelegramError(
            'Ошибка при отправке сообщения телеграм.'
        )


def get_api_answer(timestamp: int) -> Dict[str, Union[str, str]]:
    """Функция делает запрос к эндпоинту API Яндекс.Домашки.
    В случае успешного запроса возвращает ответ API,
    преобразовав его из формата JSON к типам данных Python
    """
    logging.info('Начинаем запрос к API')
    try:
        response = requests.get(
            url=ENDPOINT,
            headers=HEADERS,
            params={'from_date': timestamp}
        )
        logging.debug('Получен ответ от API')
    except requests.RequestException:
        raise exceptions.ApiRequestException('Ошибка при запросе')
    if response.status_code != HTTPStatus.OK:
        raise exceptions.InvalidResponseCode(
            'Получена ошибка при доступе к API Яндекс.Домашки. '
            f'status_code {response.status_code}'
        )
    return response.json()


def check_response(
    response: Dict[str, Union[str, str]]
) -> List[Union[str, str]]:
    """Функция проверяет ответ API на корректность.
    Если ответ API корректен - функция врзвращает список домашних работ
    """
    logging.debug('Начало проверки ответа от API')
    if not isinstance(response, dict):
        raise TypeError('Ошибка в типе ответа API')
    if 'homeworks' not in response or 'current_date' not in response:
        raise KeyError('Отсутствует ключ')
    homeworks = response.get('homeworks')
    if not isinstance(homeworks, list):
        raise TypeError('homeworks не является списком')
    return homeworks


def parse_status(homework: Dict[str, Union[str, str]]) -> str:
    """Извлекает из информации о конкретной домашней работе статус этой работы.
    В случае успеха, функция возвращает подготовленную
    для отправки в Telegram строку,
    содержащую один из вердиктов словаря HOMEWORK_VERDICTS
    """
    logging.debug('Начало извелечия статуса ДЗ')
    if 'homework_name' not in homework:
        raise KeyError('Отсутствует ключ "homework_name" в ответе API')
    if 'status' not in homework:
        raise KeyError('Отсутствует ключ "status" в ответе API')
    homework_name = homework['homework_name']
    homework_status = homework['status']
    if homework_status not in HOMEWORK_VERDICTS:
        raise Exception(f'Неизвестный статус работы: {homework_status}')
    verdict = HOMEWORK_VERDICTS[homework_status]
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def status():
    """Отправляет фото смотря какой статус дз."""
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time())
    response = get_api_answer(timestamp)
    homework_list = check_response(response)
    homework = homework_list[0]
    status = homework['status']
    if status == 'approved':
        bot.send_photo(
            chat_id=TELEGRAM_CHAT_ID,
            photo=open('2.jpeg', 'rb')
        )
    elif status == 'rejected':
        bot.send_photo(
            chat_id=TELEGRAM_CHAT_ID,
            photo=open('1.png', 'rb')
        )
    else:
        bot.send_photo(
            chat_id=TELEGRAM_CHAT_ID,
            photo=open('3.png', 'rb')
        )


def main():
    """Основная логика работы бота."""
    logging.info('Начали!')
    if not check_tokens():
        logging.critical('Отсутствует необходимое кол-во'
                         ' переменных окружения')
        sys.exit('Отсутсвуют переменные окружения')
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time())
    while True:
        try:
            response = get_api_answer(timestamp)
            homework_list = check_response(response)
            homework = homework_list[0]
            message = parse_status(homework)
            send_message(bot, message)
            timestamp = response.get('current_date')
            status()
        except IndexError:
            logging.info('Обновлений не найдено')
            timestamp = response.get('current_date')
        except TypeError as error:
            message = f'Некорректный тип данных: {error}'
            logging.error(message)
        except KeyError as error:
            message = f'Ошибка доступа по ключу: {error}'
            logging.error(message)
        except exceptions.TelegramError as error:
            message = f'Не удалось отправить сообщение в Telegram - {error}'
            logging.error(message)
        except exceptions.ConnectinError as error:
            message = f'API недоступен. Код ответа API: {error}'
            logging.error(message)
        except exceptions.ProgramError as error:
            message = f'Сбой в работе программы: {error}'
            logging.error(message)
        finally:
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s, %(levelname)s, %(message)s, %(name)s',
        filename='main.log',
        filemode='w'
    )
    main()
