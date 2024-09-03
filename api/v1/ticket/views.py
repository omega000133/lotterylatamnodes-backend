from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Sum
from django.shortcuts import get_object_or_404
from django.utils import timezone
from requests.sessions import Session
from rest_framework.generics import ListAPIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.status import HTTP_503_SERVICE_UNAVAILABLE
from rest_framework.views import APIView

from latam_nodes.delegator.models import Delegator
from latam_nodes.ticket.models import Jackpot, Participant, Ticket, Winner

from ...base.pagination import Pagination
from .serializers import ParticipantSerializer, WinnerSerializer


class TopWinnersList(ListAPIView):
    queryset = Winner.objects.filter(participant_address__isnull=False).order_by(
        "-created_at"
    )[:3]
    serializer_class = WinnerSerializer
    permission_classes = (AllowAny,)


class CheckAndUpdateAddress(APIView):
    permission_classes = (AllowAny,)

    def post(self, request, *args, **kwargs):
        address = request.data.get("address")

        # Check if the address exists in Delegator
        if not Delegator.objects.filter(address=address).exists():
            return Response({"message": "Address does not exist"}, status=404)

        delegator = get_object_or_404(Delegator, address=address)

        # Get the most recent jackpot to determine ticket cost
        latest_jackpot = (
            Jackpot.objects.order_by("-draw_date").filter(is_active=True).first()
        )
        if not latest_jackpot or latest_jackpot.ticket_cost is None:
            return Response(
                {
                    "message": "There is currently no available jackpot, but you can participate in the lottery once the jackpot is set."
                },
                status=HTTP_503_SERVICE_UNAVAILABLE,
            )

        # Calculate the number of tickets that can be purchased`
        if latest_jackpot.ticket_cost > 0:
            max_tickets = float(delegator.balance) // float(latest_jackpot.ticket_cost)
        else:
            max_tickets = 0

        if max_tickets == 0:
            with Session() as session:
                try:
                    url = f"https://api-celestia.mzonder.com/cosmos/staking/v1beta1/delegations/{address}"
                    response = session.get(url)
                    data = response.json()
                    delegation_responses = data.get("delegation_responses", [])
                    filtered_delegations = [
                        delegation
                        for delegation in delegation_responses
                        if delegation["delegation"]["validator_address"]
                        != "celestiavaloper14v4ush42xewyeuuldf6jtdz0a7pxg5fwrlumwf"
                    ]

                    total_balance = (
                        sum(
                            float(delegation["balance"]["amount"])
                            for delegation in filtered_delegations
                            if delegation["balance"]["denom"] == "utia"
                        )
                        / 1e6
                    )

                    if total_balance > 0:
                        return Response(
                            {
                                "message": f"You staked {total_balance} tia with other nodes, not Latam Nodes. If you redelegate with us, you can participate in the lottery after one week"
                            },
                            status=403,
                        )

                except Exception as e:
                    print(e)

            return Response(
                {
                    "message": "You can't participate because you haven't staked with us, or your staking amount is not enough. If you stake this week, you will be eligible to participate in the next lottery."
                },
                status=403,
            )

        # Attempt to get or create a Participant instance
        participant, created = Participant.objects.get_or_create(
            address=delegator.address,
            defaults={
                "balance": delegator.balance,
                "is_active": False,
            },
        )

        # If the participant was just created or is inactive, activate and assign tickets
        if created or not participant.is_active:
            participant.is_active = True
            participant.balance = delegator.balance
            participant.save()
            self.assign_tickets(participant, max_tickets)

        serializer = ParticipantSerializer(
            participant, data={"is_active": True}, partial=True
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=200)
        return Response(serializer.errors, status=400)

    @transaction.atomic
    def assign_tickets(self, participant, max_tickets):
        # Acquire a lock on the rows to be updated
        available_tickets = (
            Ticket.objects.filter(address__isnull=True)
            .order_by("?")
            .select_for_update(skip_locked=True)[:max_tickets]
        )

        if len(available_tickets) < max_tickets:
            return Response(
                {"message": "Not enough tickets available to assign"}, status=400
            )

        batch_size = 1000
        tickets = []

        # Assign tickets to the participant
        for ticket in available_tickets:
            ticket.address = participant
            tickets.append(ticket)
            if len(tickets) == batch_size:
                Ticket.objects.bulk_update(tickets, ["address"])
                tickets = []
        if tickets:
            # update ticket when tickets remain
            Ticket.objects.bulk_update(tickets, ["address"])


class SummaryView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        address = request.query_params.get("address", None)
        data = {}

        # Get the latest jackpot
        latest_jackpot = (
            Jackpot.objects.order_by("-draw_date").filter(is_active=True).first()
        )
        if latest_jackpot:
            data["latest_jackpot_amount"] = (
                latest_jackpot.reward * latest_jackpot.reward_percentage / 100
            )
        else:
            data["latest_jackpot_amount"] = "No jackpot available"

        # Get all delegators with a non-zero last week balance
        delegators_balance = Delegator.objects.exclude(balance=0)
        # Calculate the total balance of all such delegators
        delegate_total_balance = delegators_balance.aggregate(
            total_balance=Sum("balance")
        )["total_balance"]
        if delegate_total_balance is None:
            delegate_total_balance = 0
            
        total_ticket_count = Ticket.objects.count()
        deletation_ticket_count = delegate_total_balance // int(
            latest_jackpot.ticket_cost
        )
         
        data["total_tickets"] = min(total_ticket_count, deletation_ticket_count)

        # Get tickets count for a specific participant
        if address:
            participant_tickets = Ticket.objects.filter(
                address__address=address
            ).count()
            data["participant_tickets"] = participant_tickets
        else:
            data["participant_tickets"] = "Address not provided"

        return Response(data)


class JackpotCountdownView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        latest_jackpot = (
            Jackpot.objects.order_by("-draw_date").filter(is_active=True).first()
        )
        if latest_jackpot:
            # Assuming `draw_date` is in UTC and stored as such in the database.
            now_utc = timezone.now()
            remaining_time = latest_jackpot.draw_date - now_utc

            if remaining_time.days < 0:
                countdown = "EXPIRED"
            else:
                days, seconds = remaining_time.days, remaining_time.seconds
                hours = seconds // 3600
                minutes = (seconds % 3600) // 60
                seconds = seconds % 60
                countdown = f"{days}D : {hours}H : {minutes}M : {seconds}S"

            return Response({"countdown": countdown})
        return Response({"message": "No active jackpot found"}, status=404)


class ParticipantStatisticsView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        address = request.query_params.get("address")
        if not address:
            return Response({"error": "Address parameter is required."}, status=400)

        participant = Participant.objects.filter(address=address).first()
        if not participant:
            return Response({"error": "Participant not found."}, status=404)

        latest_jackpot = Jackpot.objects.order_by("-draw_date").first()
        ticket_cost = latest_jackpot.ticket_cost if latest_jackpot else 0
        total_tickets = Ticket.objects.filter(address=participant).count()

        # get current delegation
        with Session() as session:
            try:
                url = f"https://api-celestia.mzonder.com/cosmos/staking/v1beta1/validators/celestiavaloper14v4ush42xewyeuuldf6jtdz0a7pxg5fwrlumwf/delegations/{address}"
                response = session.get(url)
                data = response.json()
                current_balance = (
                    float(data["delegation_response"]["delegation"]["shares"]) / 1e6
                )
            except Exception as e:
                print(e)
                current_balance = participant.balance

        return Response(
            {
                "balance": participant.balance,
                "ticket_cost": ticket_cost,
                "total_tickets": total_tickets,
                "current_balance": current_balance,
            }
        )


class TicketsByAddressView(APIView):
    permission_classes = [AllowAny]
    pagination_class = Pagination()  # Use the existing pagination class

    def get(self, request):
        address = request.query_params.get("address")
        if not address:
            return Response({"error": "Address parameter is required."}, status=400)

        tickets = Ticket.objects.filter(address__address=address).order_by("hash")
        paginator = Paginator(
            tickets, self.pagination_class.get_page_size(request)
        )  # Use DRF to handle page size
        page_number = request.query_params.get(
            self.pagination_class.page_query_param, 1
        )
        page = paginator.get_page(page_number)

        if page.object_list:
            ticket_hashes = [ticket.hash for ticket in page]
            response_data = {
                "tickets": ticket_hashes,
                "count": paginator.count,
                "total_pages": paginator.num_pages,
                "next": page.next_page_number() if page.has_next() else None,
                "previous": (
                    page.previous_page_number() if page.has_previous() else None
                ),
            }
            return Response(response_data)

        return Response(
            {"error": "No tickets found for this address or invalid address."},
            status=404,
        )


class WinnerByAddressView(APIView):
    permission_classes = [AllowAny]
    pagination_class = Pagination()  # Use the existing pagination class

    def get(self, request):
        address = request.query_params.get("address")
        if not address:
            return Response({"error": "Address parameter is required."}, status=400)

        winner_list = Winner.objects.filter(participant_address__isnull=False).order_by(
            "-created_at"
        )
        paginator = Paginator(
            winner_list, self.pagination_class.get_page_size(request)
        )  # Use DRF to handle page size
        page_number = request.query_params.get(
            self.pagination_class.page_query_param, 1
        )
        page = paginator.get_page(page_number)

        serializer = WinnerSerializer(page.object_list, many=True)
        response_data = [
            {**data, "is_winner": data["participant_address"] == address}
            for data in serializer.data
        ]

        response_data = {
            "winners": response_data,
            "count": paginator.count,
            "total_pages": paginator.num_pages,
            "next": page.next_page_number() if page.has_next() else None,
            "previous": (page.previous_page_number() if page.has_previous() else None),
        }
        return Response(response_data)


class CheckAddressView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        address = request.query_params.get("address")
        if not address:
            return Response({"error": "Address parameter is required."}, status=400)

        with Session() as session:
            try:
                url = f"https://api-celestia.mzonder.com/cosmos/auth/v1beta1/accounts/{address}"
                response = session.get(url)
                data = response.json()
                account_responses = data.get("account", {})

                if not account_responses:
                    error_code = data.get("code")
                    if error_code == 2:
                        return Response(
                            {
                                "error": "Address is not validated address. Please check address again"
                            },
                            status=400,
                        )

            except Exception as e:
                print(e)
                return Response(
                    {
                        "error": "Address is not validated address. Please check address again"
                    },
                    status=400,
                )

        return Response(account_responses, status=200)


class RecentJackpotList(APIView):
    permission_classes = (AllowAny,)
    pagination_class = Pagination()
    
    def get(self, request):
        winner_list = Winner.objects.filter(jackpot__is_active=False).order_by(
        "-created_at"
    )
        paginator = Paginator(
            winner_list, self.pagination_class.get_page_size(request)
        )  # Use DRF to handle page size
        page_number = request.query_params.get(
            self.pagination_class.page_query_param, 
        )
        page = paginator.get_page(page_number)

        serializer = WinnerSerializer(page.object_list, many=True)

        response_data = {
            "results": serializer.data,
            "count": paginator.count,
            "total_pages": paginator.num_pages,
            "next": page.next_page_number() if page.has_next() else None,
            "previous": (page.previous_page_number() if page.has_previous() else None),
        }
        return Response(response_data)

