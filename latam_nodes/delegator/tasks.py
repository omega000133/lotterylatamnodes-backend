import math
import time
from datetime import datetime, timedelta, timezone
from urllib.parse import quote_plus

from celery import shared_task
from django.db import transaction
from django.db.models import Sum
from requests.sessions import Session

from latam_nodes.delegator.models import Delegator
from latam_nodes.ticket.models import Jackpot, Participant, Ticket, Winner
from latam_nodes.ticket.utils import generate_hex_hash


def fetch_delegators_data(session):
    url_base = "https://api-celestia.mzonder.com/cosmos/staking/v1beta1/validators/celestiavaloper14v4ush42xewyeuuldf6jtdz0a7pxg5fwrlumwf/delegations"
    next_key = None
    delegators_data = []
    exclude_addresses = {
        "celestia1eauf4n38gnandag9exlqrr6yy5y4852wdsfawx",
        "celestia1ll34vjd8d7r0fef04yk6xs2y6gfn009dk34we7",
    }

    while True:
        if next_key:
            encoded_next_key = quote_plus(next_key)
            url = f"{url_base}?pagination.key={encoded_next_key}"
        else:
            url = url_base

        response = session.get(url)
        data = response.json()

        for delegation in data.get("delegation_responses", []):
            address = delegation["delegation"]["delegator_address"]
            if address not in exclude_addresses:
                delegator_data = {
                    "address": address,
                    "balance": float(delegation["delegation"]["shares"]) / 1e6,
                }
                delegators_data.append(delegator_data)

        next_key = data.get("pagination", {}).get("next_key")
        if not next_key:
            break

    return delegators_data


def save_delegators(delegators_data):
    delegators = [Delegator(**data) for data in delegators_data]

    with transaction.atomic():
        Delegator.objects.all().delete()
        Delegator.objects.bulk_create(delegators, ignore_conflicts=True)


def update_ticket_cost_for_latest_jackpot():
    # Calculate the total amount of money available
    total_amount_of_money = Delegator.objects.aggregate(total_balance=Sum("balance"))[
        "total_balance"
    ]
    if total_amount_of_money is None:
        total_amount_of_money = 0  # Handle cases where no balance is available

    # Calculate the total number of tickets
    total_number_of_tickets = Ticket.objects.count()

    # Get the latest active jackpot instance
    try:
        latest_active_jackpot = Jackpot.objects.filter(is_active=True).latest(
            "draw_date"
        )
    except Jackpot.DoesNotExist:
        return  # No active jackpot exists

    # Calculate tickets to assign based on the winning percentage
    tickets_to_assign = total_number_of_tickets * (
        latest_active_jackpot.reward_percentage / 100
    )

    # Calculate total money for tickets based on the winning percentage
    total_money_for_tickets = total_amount_of_money * (
        latest_active_jackpot.reward_percentage / 100
    )

    # Calculate the cost per ticket
    if tickets_to_assign > 0:
        ticket_cost = total_money_for_tickets / tickets_to_assign
    else:
        ticket_cost = 0  # Avoid division by zero

    # Update the latest active jackpot instance with the calculated ticket cost
    latest_active_jackpot.ticket_cost = ticket_cost
    latest_active_jackpot.save()


def fetch_latest_block_data():
    # url = "https://rpc-celestia-1.latamnodes.org/block"
    url = "https://rpc-celestia.mzonder.com/block"
    closest_block = None
    closest_height = None
    closest_time_diff = timedelta.max.total_seconds()

    with Session() as session:
        start_time = datetime.now(
            timezone.utc
        )  # Asegurar que start_time es aware en UTC
        end_time = start_time + timedelta(seconds=30)

        while datetime.now(timezone.utc) < end_time:
            try:
                response = session.get(url)
                data = response.json()

                block_time_str = data["result"]["block"]["header"]["time"]

                block_time = datetime.fromisoformat(
                    block_time_str.replace("Z", "+00:00")
                )

                block_id = data["result"]["block_id"]["hash"]
                block_height = data["result"]["block"]["header"]["height"]
                time_diff = abs((block_time - start_time).total_seconds())

                if time_diff < closest_time_diff:
                    closest_block = block_id
                    closest_height = block_height
                    closest_time_diff = time_diff

            except Exception as e:
                print(f"Error fetching block data: {e}")
                continue

            time.sleep(1)  # wait for 1 second before fetching again

    return closest_block, closest_height


def check_winner_and_update_winner_model(closest_block_hash, height):
    last_four_digits = closest_block_hash[-4:]
    try:
        winning_ticket = Ticket.objects.get(hash__endswith=last_four_digits)
        participant_address = (
            winning_ticket.address.address if winning_ticket.address else None
        )

        latest_active_jackpot = Jackpot.objects.filter(is_active=True).latest(
            "draw_date"
        )
        winner, created = Winner.objects.get_or_create(
            jackpot=latest_active_jackpot,
        )
        if created:
            winner.ticket_hash = winning_ticket.hash
            winner.transaction = f"https://celestia.explorers.guru/block/{height}"
        if participant_address:
            winner.participant_address = participant_address

        winner.save()
    except Ticket.DoesNotExist or Jackpot.DoesNotExist or Exception as e:
        # No winning ticket found
        print(e)


def clear_tickets_and_set_participants_inactive():
    activated_tickets = Ticket.objects.filter(address__isnull=False)
    activated_tickets.update(address=None)
    Participant.objects.update(is_active=False)  # Set all participants as inactive
    latest_active_jackpot = Jackpot.objects.filter(is_active=True).latest("draw_date")
    latest_active_jackpot.is_active = False
    latest_active_jackpot.save()


def switch_jackpot_status():
    try:
        latest_active_jackpot = Jackpot.objects.filter(is_active=True).latest(
            "draw_date"
        )
        latest_jackpot = Jackpot.objects.latest("draw_date")

        # Ensure the latest jackpot is different from the active one
        if latest_active_jackpot.draw_date != latest_jackpot.draw_date:
            latest_active_jackpot.is_active = False
            latest_active_jackpot.save()

            latest_jackpot.is_active = True
            latest_jackpot.save()
    except Jackpot.DoesNotExist:
        pass  # Handle the case where no jackpots are found


@shared_task(name="save_delegators_task")
def save_delegators_task():
    with Session() as session:
        delegators_data = fetch_delegators_data(session)
    save_delegators(delegators_data)


@shared_task(name="check_and_save_winner_task")
def check_and_save_winner_task():
    switch_jackpot_status()
    try:
        latest_active_jackpot = Jackpot.objects.filter(is_active=True).latest(
            "draw_date"
        )
        current_time = datetime.now(timezone.utc)
        if (
            current_time > latest_active_jackpot.draw_date
            and latest_active_jackpot.is_active
        ):
            closest_block_hash, height = fetch_latest_block_data()
            check_winner_and_update_winner_model(closest_block_hash, height)
            # save_delegators_task.delay()
            clear_tickets_and_set_participants_inactive()
    except Jackpot.DoesNotExist:
        pass


@shared_task(name="create_ticket")
def create_ticket():
    Ticket.objects.all().delete()
    hash_list = generate_hex_hash()
    batch_size = 1000
    tickets = []

    for hash in hash_list:
        tickets.append(Ticket(hash=hash))
        if len(tickets) == batch_size:
            Ticket.objects.bulk_create(tickets)
            tickets = []

    # Save any remaining tickets
    if tickets:
        Ticket.objects.bulk_create(tickets)
    try:
        Participant.objects.update(is_active=False)
    except Participant.DoesNotExist:
        pass


def update_ticket_for_distribute(ticket_count, tickets, participant):
    tickets_to_update = []
    batch_size = 1000

    for i in range(min(ticket_count, len(tickets))):
        tickets[i].address = participant
        tickets_to_update.append(tickets[i])
        if len(tickets_to_update) >= batch_size:
            Ticket.objects.bulk_update(tickets_to_update, ["address"])
            tickets_to_update.clear()

    if tickets_to_update:
        Ticket.objects.bulk_update(tickets_to_update, ["address"])

    tickets = tickets[min(ticket_count, len(tickets)) :]

    return tickets


@shared_task(name="distribute_ticket_task")
def distribute_ticket():
    switch_jackpot_status()
    try:
        currente_time = datetime.now().astimezone(timezone.utc)
        latest_active_jackpot = Jackpot.objects.filter(is_active=True).latest(
            "draw_date"
        )
        time_delta = (
            latest_active_jackpot.draw_date.astimezone(timezone.utc) - currente_time
        )

        if (
            time_delta.total_seconds() / 60
            < latest_active_jackpot.start_distribute_time
        ):
            rest_tickets = Ticket.objects.filter(address__isnull=True).order_by("?")
            total_ticket_count = Ticket.objects.count()
            winnning_percetage = float(latest_active_jackpot.winning_percentage) / 100
            distributed_tickets_count = total_ticket_count - rest_tickets.count()
            
            rest_tickets_count = 0 if (distributed_tickets_count > total_ticket_count * winnning_percetage) else int(total_ticket_count * winnning_percetage - distributed_tickets_count)

            rest_tickets = rest_tickets[:rest_tickets_count]
            
            participant_list = Participant.objects.filter(is_active=True)
            
            total_amount_of_money = participant_list.aggregate(Sum("balance"))["balance__sum"]
            
            if total_amount_of_money is None:
                total_amount_of_money = 0  # Handle cases where no balance is available
            
            while len(rest_tickets) > 0:
                if(participant_list.count() < 1):
                    break
                
                for participant in participant_list:
                    ticket_count = math.ceil(
                        rest_tickets_count
                        * float(participant.balance)
                        / float(total_amount_of_money)
                    )

                    rest_tickets = update_ticket_for_distribute(
                        ticket_count=ticket_count,
                        tickets=rest_tickets,
                        participant=participant,
                    )
                    if len(rest_tickets) == 0:
                        break

    except Exception as e:
        print(e)
        pass
