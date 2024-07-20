from rest_framework_simplejwt.views import TokenObtainPairView

from api.v1.authentication.serializers import AsppiLoginSerializer


class AsppiLoginView(TokenObtainPairView):
    serializer_class = AsppiLoginSerializer