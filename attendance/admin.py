from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
import datetime
from django.utils.timezone import localtime, get_current_timezone
from django.http import HttpResponseRedirect
from attendance.models import QuarterStartDatetime, PlayerQuarterCostRule, QuarterID
from django.contrib.auth.models import User
from django.core.mail import send_mail


from .models import Game, Player, CostRule, PlayerQuarterCostRule, Payment, OtherCharge
from .transactions import QuarterCostTransaction, GameTransaction, OtherChargeTransaction, PaymentTransaction


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
                pqcr = PlayerQuarterCostRule.GetOrCreate(player,game.QuarterID())
 

class PlayerAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'initial_num_games', 'initial_balance')
    ordering = ['user__last_name', 'user__first_name']
    actions = ['send_upcoming_quarter_invoice_emails', 'send_balance_emails', 'create_new_game']
    actions_selection_counter = True

    def send_balance_emails(self, request, queryset):
        now = datetime.datetime.now(tz=get_current_timezone())
        f = open('/Users/cdebrunn/Software/djangoUWH/djangoUWH/email templates/UWH balance email.txt','r')
        message = f.read()

        for player in queryset:
            if player.user.email != '':
                # get latest PlayerQuarterCostRule for player
                latest_pqcr = PlayerQuarterCostRule.objects.filter(player=player).order_by('quarter').last()
                if latest_pqcr is not None:
                    transactions = latest_pqcr.GetTransactions()
                if len(transactions) > 0:
                    balance = transactions[-1].balance
                else:
                    balance = latest_pqcr.start_balance

                if balance > 0:
                    send_mail(subject_prefix + "UWH balance email for {} {}".format(player.user.first_name, player.user.last_name),
                              message.format(balance = balance),
                             'chris.debrunner@ieee.org',
                             [player.user.email])

                    fill_in_and_send_email(player, "DAUHC UWH debt for ", latest_pqcr, QuarterID(now), message)
                    
    send_balance_emails.short_description = "Send current balance emails"


    def send_upcoming_quarter_invoice_emails(self, request, queryset):
        now = datetime.datetime.now(tz=get_current_timezone())
        current_quarter = QuarterID(now)
        message_template_path = '/Users/cdebrunn/Software/djangoUWH/djangoUWH/email templates/'
        f = open(message_template_path + 'UWH Quarterly Player Invoice Tempate No Web Page.txt','r',encoding='utf_8')
        message = f.read()
        f = open(message_template_path + 'UWH Quarterly Player Invoice Tempate CurrentQuarterInvoiceTableRows.txt','r',encoding='utf_8')
        message_cqitr = f.read()
        f = open(message_template_path + 'UWH Quarterly Player Invoice Tempate No Web Page utf8.html','r',encoding='utf_8')
        html_message = f.read()
        f = open(message_template_path + 'UWH Quarterly Player Invoice Tempate CurrentQuarterInvoiceTableRows.html','r',encoding='utf_8')
        html_message_cqitr = f.read()
        for player in queryset:
            if player.user.email != '':
                # get latest PlayerQuarterCostRule for player
                latest_pqcr = PlayerQuarterCostRule.objects.filter(player=player, quarter__lte=current_quarter).order_by('quarter').last()
                if latest_pqcr is not None:
                    msg_values = {'QuarterlyPlanName' : str(latest_pqcr.cost_rule),
                                  'QuarterlyPlanCost' : latest_pqcr.cost_rule.quarter_cost * latest_pqcr.discount_rate,
                                  'PlayerName' : player.user.first_name + ' ' + player.user.last_name,
                                  'PaymentDueDate' : (QuarterStartDatetime(current_quarter+1).date() + datetime.timedelta(days=9)).strftime('%B %d, %Y'),
                                  'CurrentQuarterStartDate' : QuarterStartDatetime(current_quarter).date().strftime('%B %d, %Y'),
                                  'InitialBalance' : 0,
                                  'CurrentQuarterInvoiceTableRowsHTML' : '',
                                  'CurrentQuarterInvoiceTableRowsTXT' : '',
                                  'TotalBalanceDue' : 0,
                                  'username' : player.user.username}
        
                    # get transactions for this PlayerQuarterCostRule
                    transactions = latest_pqcr.GetTransactions()
                    if latest_pqcr.quarter == current_quarter:
                        msg_values['InitialBalance'] = latest_pqcr.start_balance
                        games = [ t for t in transactions if t.__class__ == GameTransaction ]
                        drop_in_games = [ t for t in games if t.amount > 0 ]
                        cqitr_values = {'QuarterlyPlanName' : msg_values['QuarterlyPlanName'],
                                        'CurrentQuarterStartDate' : msg_values['CurrentQuarterStartDate'],
                                        'CurrentQuarterlyPlanCost' : sum([t.amount for t in transactions
                                                                          if t.__class__ == QuarterCostTransaction]),
                                        'NumDropInPractices' : len(drop_in_games),
                                        'DropinCostDescr' : "${:.2f}/game".format(latest_pqcr.cost_rule.game_cost),
                                        'CurrentQuarterDropinCost' : sum([t.amount for t in drop_in_games]),
                                        'CurrentQuarterCredits' : sum([t.amount for t in transactions
                                                                       if t.__class__ == PaymentTransaction]),
                                        'CurrentQuarterOtherCharges' : sum([t.amount for t in transactions
                                                                            if t.__class__ == OtherChargeTransaction])}
                        full_price_games = [ t for t in drop_in_games if t.amount == latest_pqcr.cost_rule.game_cost ]
                        if len(drop_in_games) > len(full_price_games):
                            cqitr_values['DropinCostDescr'] += ", {:d} at half cost".format(len(drop_in_games) - len(full_price_games))
                        msg_values['CurrentQuarterInvoiceTableRowsHTML'] = html_message_cqitr.format(**cqitr_values)
                        msg_values['CurrentQuarterInvoiceTableRowsTXT'] = message_cqitr.format(**cqitr_values)
                        msg_values['TotalBalanceDue'] = (msg_values['InitialBalance'] +
                                                         sum([ t.amount for t in transactions ]) +
                                                         msg_values['QuarterlyPlanCost'])
                    else:
                        if len(transactions) > 0:
                            msg_values['InitialBalance'] = transactions[-1].balance
                        else:
                            msg_values['InitialBalance'] = latest_pqcr.start_balance
                        msg_values['TotalBalanceDue'] = msg_values['InitialBalance'] + msg_values['QuarterlyPlanCost']

                    if msg_values['TotalBalanceDue'] > 0:                            
                        send_mail("UWH upcoming quarter invoice for {} {}".format(player.user.first_name, player.user.last_name),
                                  message.format(**msg_values),
                                  'chris.debrunner@ieee.org',
                                  [player.user.email],
                                  html_message = html_message.format(**msg_values))
                    
    send_upcoming_quarter_invoice_emails.short_description = "Send upcoming quarter invoice emails"

    
    def create_new_game(self, request, queryset):
        now = datetime.datetime.now(tz=get_current_timezone())
        game = Game(starttime=now, endtime=now)
        game.save()     # to create the attendees manytomanyfield
        game.attendees.add(*queryset)
        game.save()

        # create PlayerQuarterCostRules for the players as needed
        for p in queryset:
            PlayerQuarterCostRule.GetOrCreate(p, game.QuarterID())   # will save newpqcr

        return HttpResponseRedirect("/admin/attendance/game/%d/change/" % (game.pk))
    
    create_new_game.short_description = "Create new game with selected players"

class PlayerInline(admin.StackedInline):
    model = Player
    can_delete = False

class UserAdmin(BaseUserAdmin):
    inlines = (PlayerInline, )

class CostRuleAdmin(admin.ModelAdmin):
    list_display = ('player_class', 'is_visitor', 'quarterly_games_per_week', 'game_cost', 'quarter_cost', 'free_games', 'half_cost_games', 'first_valid_quarter', 'is_default')
    ordering = ['first_valid_quarter', '-is_visitor', '-player_class', 'quarterly_games_per_week']

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
    list_display = ('quarter_start_date', 'player', 'cost_rule', 'prorate', 'discount_rate', 'formatted_start_balance')
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
