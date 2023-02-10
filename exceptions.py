class TelegramError(Exception):
    """Сообщение не отправляется в Telegram."""

    pass


class InvalidResponseCode(Exception):
    """Запрос к API Яндекс.Домашки не проходит."""

    pass


class ConnectinError(Exception):
    """API недоступен, но отвечает."""

    pass


class ApiRequestException(Exception):
    """Получена ошибка при запросе к API."""

    pass


class ProgramError(Exception):
    """Любой другой сбой в программе."""

    pass
