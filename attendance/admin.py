from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
import datetime
from django.utils.timezone import localtime, get_current_timezone
from django.http import HttpResponseRedirect
from attendance.models import QuarterStartDatetime, PlayerQuarterCostRule, QuarterID
from django.contrib.auth.models import User
from django.core.mail import send_mail


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
    actions = ['create_player_PQCRs']
    actions_selection_counter = True

    def create_player_PQCRs(self, request, queryset):
        for game in queryset:
            for player in game.attendees.all():
                pqcr = PlayerQuarterCostRule.objects.filter(player=player,quarter=game.QuarterID())
                if pqcr:
                    pass
                else:
                    lastpqcr = PlayerQuarterCostRule.objects.filter(player=player,quarter__lt=game.QuarterID()).order_by('quarter').last()
                    if lastpqcr:
                        new_cost_rule = lastpqcr.cost_rule
                    else:
                        new_cost_rule = CostRule.objects.get(player_class=CostRule.REGULAR,is_visitor=false)

                    newpqcr = PlayerQuarterCostRule(cost_rule=new_cost_rule, \
                                                    player=player,       \
                                                    quarter=game.QuarterID())
                    newpqcr.Update()
                    newpqcr.save()


class PlayerAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'initial_num_games', 'initial_balance')
    ordering = ['user__last_name', 'user__first_name']
    actions = ['send_balance_emails', 'create_new_game']
    actions_selection_counter = True

    def send_balance_emails(self, request, queryset):
        now = datetime.datetime.now(tz=get_current_timezone())
        message = """\
This is an automated email sent by the Denver Area Underwater Hockey Club (DAUHC)
attendance web server to let you know what you currently owe for practices. You can
view your attendance history and balance at

http://uwhockey.org/colorado/Attendance.html

where your login name is {username}. If you do not know your password (or if you have
never used your login) click on "Forgotten your password or username?" to set a new
password. This attendance web page also allows you to change your quarterly plan, but
only during the first four weeks of each quarter. Each quarter your quarterly plan is
automatically set to be the same as your quarterly plan from the previous quarter. 

You can pay by giving Chris Debrunner cash or a check made out to DAUHC, or you
can pay by paypal to: denverUWH@gmail.com. You must make a "personal" money transfer
from your Paypal account or bank account to avoid Paypal fees. We will ask you to cover
any fees incurred by mistake or from using a credit card.

You currently owe ${balance:.2f} (go to https://www.paypal.me/denveruwh/{balance:.2f}
to pay via PayPal now). This includes both your Carmody, VMAC, and EPIC practices. ${extraMessage}
"""
        thisQuarterMessage = """\
 This
does not include your quarterly fees for the current quarter, which will be billed when
you play your first game in the quarter. With this quarter's quarterly fees you owe
${thisquarterbalance:.2f} (go to https://www.paypal.me/denveruwh/{thisquarterbalance:.2f}
to pay by PayPal now).
"""

        for player in queryset:
            if player.user.email != '':
                # get latest PlayerQuarterCostRule for player
                latest_pqcr = PlayerQuarterCostRule.objects.filter(player=player).order_by('quarter').last()
                if latest_pqcr is not None:
                    # get transactions for this PlayerQuarterCostRule
                    transactions = latest_pqcr.GetTransactions()
                    if len(transactions) > 0:
                        balance = transactions[-1].balance
                    else:
                        balance = latest_pqcr.start_balance

                    if balance > 0:
                        extraMessage = ""
                        if (latest_pqcr.quarter != QuarterID(now)) and (latest_pqcr.cost_rule.quarter_cost > 0):
                            extraMessage = thisQuarterMessage.format(thisquarterbalance = balance + latest_pqcr.cost_rule.quarter_cost)
                            
                        send_mail("DAUHC UWH debt for {} {}".format(player.user.first_name, player.user.last_name),
                                  message.format(username=player.user.username, balance=balance, extraMessage=extraMessage),
                                  'chris.debrunner@ieee.org', [player.user.email])
                    
    send_balance_emails.short_description = "Send current balance emails"



    def create_new_game(self, request, queryset):
        now = datetime.datetime.now(tz=get_current_timezone())
        game = Game(starttime=now, endtime=now)
        game.save()     # to create the attendees manytomanyfield
        game.attendees.add(*queryset)
        game.save()

        # create PlayerQuarterCostRules for the players as needed
        for p in queryset:
            lastpqcr = PlayerQuarterCostRule.objects.filter(player=p).order_by('quarter').last()
            if lastpqcr == None:
                newpqcr = PlayerQuarterCostRule(player=p, quarter=QuarterID(now))
                PlayerQuarterCostRule.UpdatePlayerQuarterCostRules([newpqcr])   # will save newpqcr
            elif lastpqcr.quarter != QuarterID(now):
                # need to create a new PlayerQuarterCostRule copied from previous
                newpqcr = PlayerQuarterCostRule(cost_rule=lastpqcr.cost_rule,
                                                player=p,
                                                quarter=QuarterID(now))
                PlayerQuarterCostRule.UpdatePlayerQuarterCostRules([lastpqcr, newpqcr])   # will save newpqcr

        return HttpResponseRedirect("/admin/attendance/game/%d/change/" % (game.pk))
    
    create_new_game.short_description = "Create new game with selected players"

class PlayerInline(admin.StackedInline):
    model = Player
    can_delete = False

class UserAdmin(BaseUserAdmin):
    inlines = (PlayerInline, )

class CostRuleAdmin(admin.ModelAdmin):
    list_display = ('player_class', 'is_visitor', 'quarterly_games_per_week', 'game_cost', 'quarter_cost', 'free_games', 'half_cost_games')
    ordering = ['-is_visitor', '-player_class', 'quarterly_games_per_week']

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
admin.site.register(CostRule, CostRuleAdmin)
admin.site.register(PlayerQuarterCostRule, PlayerQuarterCostRuleAdmin)
admin.site.register(Payment, PaymentAdmin)
admin.site.register(OtherCharge, OtherChargeAdmin)
admin.site.unregister(User)
admin.site.register(User, UserAdmin)
