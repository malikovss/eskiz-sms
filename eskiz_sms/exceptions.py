class EskizException(Exception):
    def __init__(self, message=None, status=None):
        self.status = status
        self.message = message
        message = str(message) if message else ''
        if status:
            message += f" ({status})"
        super(EskizException, self).__init__(message.strip())


class BadRequest(EskizException):
    pass


class InvalidCredentials(EskizException):
    pass


class TokenBlackListed(EskizException):
    pass


class TokenInvalid(EskizException):
    pass


class UpdateRetryCountExceeded(EskizException):
    pass


class ContactNotFound(EskizException):
    pass
