import math
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.generics import ListAPIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.status import HTTP_503_SERVICE_UNAVAILABLE
from rest_framework.views import APIView
from requests.sessions import Session

from latam_nodes.delegator.models import Delegator
from latam_nodes.ticket.models import Winner, Participant, Jackpot, Ticket
from latam_nodes.ticket.utils import get_node_reward
from .serializers import WinnerSerializer, ParticipantSerializer
from ...base.pagination import Pagination


class TopWinnersList(ListAPIView):
    queryset = Winner.objects.all().order_by('-created_at')[:3]
    serializer_class = WinnerSerializer
    permission_classes = (AllowAny,)


from django.db import transaction


class CheckAndUpdateAddress(APIView):
    permission_classes = (AllowAny,)

    def post(self, request, *args, **kwargs):
        address = request.data.get('address')

        # Check if the address exists in Delegator
        if not Delegator.objects.filter(address=address).exists():
            return Response({'message': 'Address does not exist'}, status=404)

        delegator = get_object_or_404(Delegator, address=address)

        # Get the most recent jackpot to determine ticket cost
        latest_jackpot = Jackpot.objects.order_by('-draw_date').filter(is_active=True).first()
        if not latest_jackpot or latest_jackpot.ticket_cost is None:
            return Response({'message': 'The service is currently unavailable.'}, status=HTTP_503_SERVICE_UNAVAILABLE)

        # Calculate the number of tickets that can be purchased`
        if latest_jackpot.ticket_cost > 0:
            max_tickets = float(delegator.balance) // float(latest_jackpot.ticket_cost)
        else:
            max_tickets = 0

        if max_tickets == 0:
            return Response({'message': "You can't participate as your balance doesn't allow purchasing any tickets."},
                            status=403)
            
        # get current delegation
        with Session() as session:
            try:
                url = f"https://api-celestia.mzonder.com/cosmos/staking/v1beta1/validators/celestiavaloper14v4ush42xewyeuuldf6jtdz0a7pxg5fwrlumwf/delegations/{address}"
                response = session.get(url)
                data = response.json()
                current_balnce = data["delegation_response"]["delegation"]["shares"]
            except Exception as e:
                print(e)
                current_balnce = delegator.balance
        

        # Attempt to get or create a Participant instance
        participant, created = Participant.objects.get_or_create(
            address=delegator.address,
            defaults={
                'balance': delegator.balance,
                'is_active': False,
                'current_balance': current_balnce
            }
        )

        # If the participant was just created or is inactive, activate and assign tickets
        if created or not participant.is_active:
            participant.is_active = True
            participant.save()
            self.assign_tickets(participant, max_tickets)

        serializer = ParticipantSerializer(participant, data={'is_active': True}, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=200)
        return Response(serializer.errors, status=400)

    @transaction.atomic
    def assign_tickets(self, participant, max_tickets):
        # Acquire a lock on the rows to be updated
        available_tickets = Ticket.objects.filter(address__isnull=True).order_by("?").select_for_update(skip_locked=True)[
                            :max_tickets]

        if len(available_tickets) < max_tickets:
            return Response({'message': 'Not enough tickets available to assign'}, status=400)

        # Assign tickets to the participant
        for ticket in available_tickets:
            ticket.address = participant

        # Use bulk_update to save all tickets at once
        Ticket.objects.bulk_update(available_tickets, ['address'])


class SummaryView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        address = request.query_params.get('address', None)
        data = {}

        # Get the latest jackpot
        latest_jackpot = Jackpot.objects.order_by('-draw_date').filter(is_active=True).first()
        if latest_jackpot:
            data['latest_jackpot_amount'] = latest_jackpot.reward
        else:
            data['latest_jackpot_amount'] = 'No jackpot available'

        # Get total ticket count
        total_tickets = Ticket.objects.count()
        data['total_tickets'] = total_tickets

        # Get tickets count for a specific participant
        if address:
            participant_tickets = Ticket.objects.filter(address__address=address).count()
            data['participant_tickets'] = participant_tickets
        else:
            data['participant_tickets'] = 'Address not provided'

        return Response(data)


class JackpotCountdownView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        latest_jackpot = Jackpot.objects.order_by('-draw_date').filter(is_active=True).first()
        if latest_jackpot:
            # Assuming `draw_date` is in UTC and stored as such in the database.
            now_utc = timezone.now()
            remaining_time = latest_jackpot.draw_date - now_utc

            if remaining_time.days < 0:
                countdown = 'EXPIRED'
            else:
                days, seconds = remaining_time.days, remaining_time.seconds
                hours = seconds // 3600
                minutes = (seconds % 3600) // 60
                seconds = seconds % 60
                countdown = f"{days}D : {hours}H : {minutes}M : {seconds}S"

            return Response({'countdown': countdown})
        return Response({'message': 'No active jackpot found'}, status=404)


class ParticipantStatisticsView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        address = request.query_params.get('address')
        if not address:
            return Response({'error': 'Address parameter is required.'}, status=400)

        participant = Participant.objects.filter(address=address).first()
        if not participant:
            return Response({'error': 'Participant not found.'}, status=404)

        latest_jackpot = Jackpot.objects.order_by('-draw_date').first()
        ticket_cost = latest_jackpot.ticket_cost if latest_jackpot else 0
        total_tickets = Ticket.objects.filter(address=participant).count()

        return Response({
            'balance': participant.balance,
            'ticket_cost': ticket_cost,
            'total_tickets': total_tickets,
            'current_balance': participant.current_balance
        })


class TicketsByAddressView(APIView):
    permission_classes = [AllowAny]
    pagination_class = Pagination()  # Use the existing pagination class

    def get(self, request):
        address = request.query_params.get('address')
        if not address:
            return Response({'error': 'Address parameter is required.'}, status=400)

        tickets = Ticket.objects.filter(address__address=address).order_by('hash')
        paginator = Paginator(tickets, self.pagination_class.get_page_size(request))  # Use DRF to handle page size
        page_number = request.query_params.get(self.pagination_class.page_query_param, 1)
        page = paginator.get_page(page_number)

        if page.object_list:
            ticket_hashes = [ticket.hash for ticket in page]
            response_data = {
                'tickets': ticket_hashes,
                'count': paginator.count,
                'total_pages': paginator.num_pages,
                'next': page.next_page_number() if page.has_next() else None,
                'previous': page.previous_page_number() if page.has_previous() else None
            }
            return Response(response_data)

        return Response({'error': 'No tickets found for this address or invalid address.'}, status=404)
