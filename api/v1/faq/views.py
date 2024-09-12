from rest_framework.permissions import AllowAny
from rest_framework.generics import ListAPIView

from latam_nodes.faq.models import Faq

from .serializers import FaqSerializer


class FaqList(ListAPIView):
    queryset = Faq.objects.all().order_by(
        "priority", "-updated_at"
    )
    serializer_class = FaqSerializer
    permission_classes = (AllowAny,)

