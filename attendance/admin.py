from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
import datetime
from django.utils.timezone import localtime
from attendance.models import QuarterStartDatetime, PlayerQuarterCostRule
from django.contrib.auth.models import User


from .models import Game, Player, CostRule, PlayerQuarterCostRule, Payment, OtherCharge

class GameAdmin(admin.ModelAdmin):
    list_display = ('starttime', 'pool', 'player_count')
    list_filter = ['starttime', 'pool']
    filter_horizontal = ['attendees']
    date_hierarchy = 'starttime'
    ordering = ['-starttime']
    fieldsets = [
        ('Date',  {'fields': ['starttime', 'endtime']}),
        (None,    {'fields': ['pool', 'attendees']}),
        ('Other', {'fields': ['notes', 'shared_time_minutes'], 'classes': ['collapse']}),
    ]

class PlayerAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'initial_num_games', 'initial_balance')
    ordering = ['user__last_name', 'user__first_name']

class PlayerInline(admin.StackedInline):
    model = Player
    can_delete = False

class UserAdmin(BaseUserAdmin):
    inlines = (PlayerInline, )

class CostRuleAdmin(admin.ModelAdmin):
    list_display = ('player_class', 'quarterly_games_per_week')

class QuarterListFilter(admin.SimpleListFilter):
    title = 'Quarter Start Date'
    parameter_name = 'quarter'

    def lookups(self, request, model_admin):
        quarters = set(PlayerQuarterCostRule.objects.values_list('quarter', flat=True))
        return [(q, str(localtime(QuarterStartDatetime(q)).date())) for q in quarters]

    def queryset(self, request, queryset):
        if self.value() == None:
            return queryset
        else:
            return queryset.filter(quarter=self.value())

class PlayerQuarterCostRuleAdmin(admin.ModelAdmin):
    list_display = ('quarter_start_date', 'player', 'cost_rule', 'formatted_start_balance')
    list_filter = (QuarterListFilter,)
    #date_hierarchy = 'quarter_start_date'
    ordering = ['-quarter', 'player__user__last_name', 'player__user__first_name']

class PaymentAdmin(admin.ModelAdmin):
    list_display = ('time', 'player', 'formatted_amount', 'payment_type', 'reference')
    list_filter = ['time', 'payment_type']
    date_hierarchy = 'time'
    ordering = ['-time']

class OtherChargeAdmin(admin.ModelAdmin):
    list_display = ('time', 'player', 'formatted_amount', 'remarks')
    list_filter = ['time']
    date_hierarchy = 'time'
    ordering = ['-time']

# Register your models here.

admin.site.register(Game, GameAdmin)
admin.site.register(Player, PlayerAdmin)
admin.site.register(CostRule)
admin.site.register(PlayerQuarterCostRule, PlayerQuarterCostRuleAdmin)
admin.site.register(Payment, PaymentAdmin)
admin.site.register(OtherCharge, OtherChargeAdmin)
admin.site.unregister(User)
admin.site.register(User, UserAdmin)
