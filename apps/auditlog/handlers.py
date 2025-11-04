# apps/auditlog/handlers.py
import logging

class DatabaseLogHandler(logging.Handler):
    def emit(self, record):
        try:
            # Importación tardía para evitar problemas de dependencia circular
            from .models import LogEntry
            
            # Obtener el usuario y la IP de la solicitud si están disponibles
            user = getattr(record, 'user', None)
            ip_address = getattr(record, 'ip_address', None)

            # Crear la entrada en la base de datos
            LogEntry.objects.create(
                user=user,
                ip_address=ip_address,
                level=record.levelname,
                action=self.format(record)  # El mensaje formateado
            )
        except Exception:
            # Evitar bucles infinitos si hay un error al guardar en la BD
            pass