from django.contrib import admin

from .models import Participant, Ticket, Jackpot, Winner

admin.site.register(Participant, )
admin.site.register(Ticket, )
admin.site.register(Jackpot, )
admin.site.register(Winner, )
