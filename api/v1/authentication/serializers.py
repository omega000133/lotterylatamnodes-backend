from datetime import datetime

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from rest_framework import exceptions
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from config import settings

User = get_user_model()


class AsppiLoginSerializer(TokenObtainPairSerializer):

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        user.last_login = datetime.now()
        user.save(update_fields=['last_login'])
        token['login_date'] = user.last_login.timestamp()
        return token

    def validate(self, attrs):
        data = super(AsppiLoginSerializer, self).validate(attrs)
        data.update({'usuario': self.user.username})
        data.update({'email': self.user.email})
        data.update({'nombres': self.user.get_full_name()})

        if self.user.is_superuser:
            self.user.last_login = datetime.now()
            self.user.save()
            return data

        request = self.context["request"]
        username = request.data.get("username")

        user = User.objects.get(username=username)

        grupos_permitidos = Group.objects.all() \
            .exclude(name=settings.NOMBRE_ROL_USUARIOS).values_list('name', flat=True)

        if not user.groups.filter(name__in=grupos_permitidos).exists():
            error_message = "Su clave es correcta, pero no tiene permisos para ingresar."
            # raise exceptions.AuthenticationFailed(error_message, error_name)
            raise exceptions.PermissionDenied(error_message)

        grupos_usuario = []
        for grupo in user.groups.all():
            grupos_usuario.append(grupo.name)
        data.update({'mg': grupos_usuario})

        return data
