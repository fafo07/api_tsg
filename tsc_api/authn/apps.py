from django.apps import AppConfig


class AuthnConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'tsc_api.authn'

    def ready(self):
        from tsc_api.authn import schema  # noqa: F401
