from django.contrib import admin

from .models import Participant, Ticket, Jackpot, Winner

admin.site.register(Participant, )
admin.site.register(Ticket, )

@admin.register(Jackpot)
class JackpotAdmin(admin.ModelAdmin):
    exclude = ["total_reward", "current_reward",]

admin.site.register(Winner, )
