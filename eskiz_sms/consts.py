TOKEN_GENERATED = "token_generated"
INVALID_TOKEN = "invalid"
VALID_TOKEN = "valid"
BASE_URL = "https://notify.eskiz.uz/api"


class ApiPaths:
    GET_TOKEN = "/auth/login"
    UPDATE_TOKEN = "/auth/refresh"
    DELETE_TOKEN = "/auth/invalidate"
    GET_USER = "/auth/user"
    ADD_CONTACT = "/contact"
    CONTACT = "api/contact/{id}"
    SEND_SMS = "/message/sms/send"
