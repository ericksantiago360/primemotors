from django.apps import AppConfig


class ItemConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'item'

    def ready(self):
        from . import signals  # noqa: F401  registra las señales de borrado de imágenes
