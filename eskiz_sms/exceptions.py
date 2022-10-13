class EskizException(Exception):
    def __init__(self, *args, status=None, message=None):
        self.status = status
        self.message = message
        super(EskizException, self).__init__(*args)


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
