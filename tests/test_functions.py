from tests import config


class TestFunctions:
    def test_property_user(self):
        eskiz = config.get_eskiz_instance()
        user = eskiz.user
        assert user.email == config.EMAIL
