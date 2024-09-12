from rest_framework import serializers

from latam_nodes.faq.models import Faq


class FaqSerializer(serializers.ModelSerializer):
    class Meta:
        model = Faq
        fields = ["title", "content"]
