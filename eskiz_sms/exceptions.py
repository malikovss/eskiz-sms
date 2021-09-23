class EskizException(Exception):
    pass


class BadRequest(EskizException):
    pass


class InvalidCredentials(EskizException):
    pass


class TokenBlackListed(EskizException):
    pass
