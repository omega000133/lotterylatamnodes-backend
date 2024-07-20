from django.urls import include, path

from api.v1 import urls as urls_api_v1


urlpatterns = [
    path("v1/", include(urls_api_v1)),
]


