from django.urls import path
from rest_framework import routers

from api.v1.faq.views import (
    FaqList,
)

router = routers.DefaultRouter()

urlpatterns = [
    path("faqs/", FaqList.as_view(), name="faqs"),
]
