from rest_framework import serializers

from latam_nodes.ticket.models import Jackpot, Participant, Ticket, Winner


class WinnerTicketSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ticket
        fields = ["hash"]


class JackpotSerializer(serializers.ModelSerializer):
    draw_date = serializers.SerializerMethodField()

    class Meta:
        model = Jackpot
        fields = ["reward", "draw_date", "reward_percentage"]

    def get_draw_date(self, obj):
        return obj.draw_date


class WinnerSerializer(serializers.ModelSerializer):
    jackpot = JackpotSerializer(read_only=True)

    class Meta:
        model = Winner
        fields = ["ticket_hash", "jackpot", "participant_address", "transaction"]


class ParticipantSerializer(serializers.ModelSerializer):
    class Meta:
        model = Participant
        fields = ["address", "balance", "is_active"]

    def create(self, validated_data):
        instance, created = Participant.objects.update_or_create(
            address=validated_data["address"],
            defaults={"balance": validated_data.get("balance", 0)},
        )
        return instance
