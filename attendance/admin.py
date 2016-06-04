from django.contrib import admin

from .models import Game, Player, CostRule, PlayerQuarterCostRule, Payment, OtherCharge

class GameAdmin(admin.ModelAdmin):
    fieldsets = [
        ('Date',  {'fields': ['starttime', 'endtime']}),
        (None,    {'fields': ['pool', 'attendees']}),
        ('Other', {'fields': ['notes', 'shared_time_minutes'], 'classes': ['collapse']}),
    ]

# Register your models here.

admin.site.register(Game, GameAdmin)
admin.site.register(Player)
admin.site.register(CostRule)
admin.site.register(PlayerQuarterCostRule)
admin.site.register(Payment)
admin.site.register(OtherCharge)
