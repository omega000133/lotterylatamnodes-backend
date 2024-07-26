from django.apps import AppConfig


class TicketConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'latam_nodes.ticket'
    
    def ready(self) -> None:
        import latam_nodes.ticket.signals