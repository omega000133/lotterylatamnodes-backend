from django.urls import path
from rest_framework import routers

from api.v1.ticket.views import TopWinnersList, CheckAndUpdateAddress, SummaryView, JackpotCountdownView, \
    ParticipantStatisticsView, TicketsByAddressView

router = routers.DefaultRouter()

urlpatterns = [
    path('top-winners/', TopWinnersList.as_view(), name='top-winners'),
    path('check-update-address/', CheckAndUpdateAddress.as_view(), name='check-update-address'),
    path('summary/', SummaryView.as_view(), name='summary'),
    path('countdown/', JackpotCountdownView.as_view(), name='countdown'),
    path('participant-statistics/', ParticipantStatisticsView.as_view(), name='participant-statistics'),
    path('tickets-by-address/', TicketsByAddressView.as_view(), name='tickets-by-address'),
]
