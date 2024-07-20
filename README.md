Instala las dependencias del proyecto:

```bash
pip install -r requirements/dev.txt
```

## Crear un Superusuario

Ejecuta los siguientes comandos para crear un superusuario:

```bash
python manage.py createsuperuser
```

Sigue las instrucciones en pantalla para configurar el superusuario.

## Correr el Servidor

Para correr el servidor de desarrollo, utiliza el siguiente comando:

```bash
python manage.py runserver
```

## Configuración de Celery y Redis

### Levantar el Servidor Redis

En una terminal separada, ejecuta:

```bash
redis-server
```

### Iniciar el Worker de Celery

En otra terminal, ejecuta:

```bash
celery -A config worker -l info
```

### Iniciar el Beat de Celery

En otra terminal adicional, ejecuta:

```bash
celery -A config beat -l info
```

### Iniciar el Beat de Celery con Scheduler de Django

En otra terminal adicional, ejecuta:

```bash
celery -A config beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler
```

## Alimentar la Tabla de Delegadores

Para alimentar la tabla de delegadores, abre el shell de Django y ejecuta la tarea:

```bash
python manage.py shell
```

Dentro del shell de Django, ejecuta:

```python
from latam_nodes.delegator.tasks import save_delegators_task

# Ejecuta la tarea de manera asíncrona
save_delegators_task.delay()

# O ejecuta la tarea de manera síncrona
save_delegators_task.apply()
```