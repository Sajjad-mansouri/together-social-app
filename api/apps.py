from django.apps import AppConfig


class ApiConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'api'

    def ready(self):
        # Implicitly connect signal handlers decorated with @receiver.
        print('ready')
        from . import signals
