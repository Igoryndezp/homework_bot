class TelegramError(Exception):
    """Сообщение не отправляется в Telegram."""


class InvalidResponseCode(Exception):
    """Запрос к API Яндекс.Домашки не проходит."""


class ConnectinError(Exception):
    """API недоступен, но отвечает."""


class ApiRequestException(Exception):
    """Получена ошибка при запросе к API."""


class ProgramError(Exception):
    """Любой другой сбой в программе."""
