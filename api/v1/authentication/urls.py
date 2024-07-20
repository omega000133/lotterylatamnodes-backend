from django.urls import path, include
from rest_framework import routers

from .views import AsppiLoginView

router = routers.DefaultRouter()

urlpatterns = [
    path('', include(router.urls)),
    path("login/", AsppiLoginView.as_view(), name="token_obtain_pair"),
]
