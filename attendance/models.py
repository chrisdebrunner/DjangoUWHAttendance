from django.db import models
import datetime
from django.utils import timezone
from attendance.transactions import Transaction
from operator import attrgetter
from django.contrib.auth.models import User

# not sure why this code is still needed, but the server complains if newuser is
# missing saying that it is needed in migration 0012_player_user.py on line 22
def getnewuser():
    f = open('number','r')
    v = int(f.read())
    f.close()
    return v

def setnewuser(v):
    f = open('number','w')
    f.write(str(v))
    f.close()    

def newuser():
    v = getnewuser() + 1
    setnewuser(v)
    print('using newuser', str(v))
    return v

class Player(models.Model):
    user = models.OneToOneField(User)
    initial_num_games = models.IntegerField(default=0)
    initial_balance = models.FloatField(default=0)
    notes = models.CharField(blank=True, max_length=100)

    def full_name(self):
        return self.user.first_name + ' ' + self.user.last_name
    full_name.short_description = 'Player Name'
    full_name.admin_oder_field = 'user.last_name'    
    
    def formatted_initial_balance(self):
        return '${:>8.2f}'.format(self.initial_balance)
    formatted_initial_balance.short_description = 'Initial Balance'
    formatted_initial_balance.admin_oder_field = 'initial_balance'
    
    def __str__(self):
        return self.user.first_name + ' ' + self.user.last_name


class Game(models.Model):
    CARMODY = 1
    VMAC = 2
    POOL_CHOICES = (
        (CARMODY, 'Carmody'),
        (VMAC, 'VMAC'),
    )
    pool = models.IntegerField(choices=POOL_CHOICES, default=CARMODY)
    starttime = models.DateTimeField()
    endtime = models.DateTimeField()
    shared_time_minutes = models.IntegerField(default=0)
    attendees = models.ManyToManyField(Player, blank=True)
    notes = models.CharField(blank=True, max_length=100)

    def player_count(self):
        return self.attendees.count()

    def QuarterID(self):
        return QuarterID(self.starttime)

    def QuarterStartDatetime(self):
        return QuarterStartDatetime(self.QuarterID())
    
    def QuarterStartDate(self):
        return QuarterStartDatetime(self.QuarterID()).date()
    
    def __str__(self):
        return 'game at ' + self.get_pool_display() + ' on ' + timezone.localtime(self.starttime).ctime() + ' with ' + str(self.player_count()) + ' players'


class CostRule(models.Model):
    REGULAR = 1
    STUDENT = 2
    JUNIOR = 3
    PLAYER_CLASS_CHOICES = (
        (REGULAR, 'regular player'),
        (STUDENT, 'student'),
        (JUNIOR, 'junior player'),
    )
    GAMES_PER_WEEK_CHOICES = (
        (0, 'no quarterly'),
        (1, 'one game per week quarterly'),
        (2, 'two games per week quarterly'),
        (3, 'three games per week quarterly'),
        (4, 'four games per week quarterly'),
    )
    player_class = models.PositiveSmallIntegerField(choices=PLAYER_CLASS_CHOICES, default=REGULAR)
    is_visitor = models.BooleanField(default=False)
    quarterly_games_per_week = models.PositiveSmallIntegerField(choices=GAMES_PER_WEEK_CHOICES, default=0)
    game_cost = models.FloatField(default=0.0)
    quarter_cost = models.FloatField(default=0.0)
    covered_games_per_quarter = models.SmallIntegerField(default=0)
    free_games = models.SmallIntegerField(default=0)
    half_cost_games = models.SmallIntegerField(default=0)
    
    class Meta:
        unique_together = ("player_class", "is_visitor", "quarterly_games_per_week")

    def formatted_game_cost(self):
        return '${:>8.2f}'.format(self.game_cost)
    formatted_game_cost.short_description = 'Game Cost'
    formatted_game_cost.admin_oder_field = 'game_cost'

    def formatted_quarter_cost(self):
        return '${:>8.2f}'.format(self.quarter_cost)
    formatted_quarter_cost.short_description = 'Quarter Cost'
    formatted_quarter_cost.admin_oder_field = 'quarter_cost'

    def __str__(self):
        if self.is_visitor:
            return 'visitor ' + self.get_player_class_display()
        else:
            return self.get_player_class_display() + ' ' + self.get_quarterly_games_per_week_display()

    
    
def QuarterStartDatetime(id):
    return datetime.datetime(2000 + ((id-1) // 4), 3 * ((id-1) % 4) + 1, 1, tzinfo=timezone.get_current_timezone())

def QuarterID(dt):
    return 4 * (dt.year - 2000) + ((dt.month-1) // 3) + 1

def QuarterDatetimeRange(id):
    "return the datetime range in the given quarter"
    return QuarterStartDatetime(id), QuarterStartDatetime(id+1) - datetime.datetime.resolution

def QuarterWeekNumber(id, dt):
    "return the week number of the datetime dt in the quarter with the given id"
    qsd = QuarterStartDatetime(id)
    return (dt.toordinal() - qsd.toordinal() + (qsd.weekday() - PlayerQuarterCostRule.WEEK_START_DAY)%7) // 7

def UpdateAllPlayerQuarterCostRules(quarter_id, max_lookback=1, players=None):
    "Call Update on all PlayerQuarterCostRules in the given quarter"

    if players == None:
        pqcrs = PlayerQuarterCostRule.objects.filter(quarter=quarter_id)
    else:
        pqcrs = PlayerQuarterCostRule.objects.filter(quarter=quarter_id, player__in=players)

    for pqcr in pqcrs:
        pqcr.Update(max_lookback)


class PlayerQuarterCostRule(models.Model):
    cost_rule = models.ForeignKey(CostRule)
    player = models.ForeignKey(Player)
    quarter = models.PositiveSmallIntegerField(default=0)
    start_balance = models.FloatField(default=0.0)
    start_num_games = models.PositiveSmallIntegerField(default=0)
    prorate = models.FloatField(default=1.0)
    WEEK_START_DAY = 6         # starting day of the week, Mon=0, Tue=1, ..., Sun = 6
    
    class Meta:
        unique_together = ("player", "quarter")

    def Update(self, max_lookback=None, pqcrs=None):
        "Update start_balance and start_num_games based on earlier quarters' info, transactions, and game counts"

        # if pqcrs is not specified, get all earlier PlayerQuarterCostRules for current player including current
        if pqcrs == None:
            pqcrs = PlayerQuarterCostRule.objects.filter(player=self.player, quarter__lte=self.quarter).order_by('quarter')

        first_pqcr = PlayerQuarterCostRule.objects.filter(player=pqcrs[0].player).order_by('quarter').first()

        # trim the pqcrs list if it is longer than max_lookback
        # max_lookback == None means look back as far a possible
        if max_lookback != None and len(pqcrs) > max_lookback:
            pqcrs = pqcrs[-max_lookback:]

        # make sure first pqcr is initialized to the player's start balance and num games
        if pqcrs[0] == first_pqcr:
            pqcrs[0].start_balance = self.player.initial_balance
            pqcrs[0].start_num_games = self.player.initial_num_games

        balance = pqcrs[0].start_balance + sum(pqcrs[0].GetTransactions())
        num_games = pqcrs[0].start_num_games + pqcrs[0].player.game_set.filter(starttime__range=QuarterDatetimeRange(pqcrs[0].quarter)).count()

        for pqcr in pqcrs[1:]:
            pqcr.start_balance = balance
            pqcr.start_num_games = num_games
            pqcr.save()

            if pqcr != pqcrs.last():
                balance += sum(pqcr.GetTransactions())
                num_games += pqcr.player.game_set.filter(starttime__range=QuarterDatetimeRange(pqcr.quarter)).count()
                

    def GetTransactions(self):
        "return a date-sorted list of all transactions covered by this PlayerQuarterCostRule"

        transactions = []

        # create a transaction for the quarterly cost
        if self.cost_rule.quarter_cost > 0:
            transactions.append(Transaction(QuarterStartDatetime(self.quarter), self.cost_rule.quarter_cost * self.prorate, "Quarterly cost"))

        prev_game_week = -1
        games_in_week = 0
        player_total_games = self.start_num_games
        
        # create transactions for all games in this quarter
        for game in self.player.game_set.filter(starttime__range=QuarterDatetimeRange(self.quarter)).order_by('starttime'):
            game_week = QuarterWeekNumber(self.quarter, game.starttime)
            if game_week == prev_game_week:
                games_in_week += 1
            else:
                prev_game_week = game_week
                games_in_week = 1

            player_total_games += 1

            if player_total_games > self.cost_rule.free_games:
                if games_in_week > self.cost_rule.quarterly_games_per_week:
                    cost = self.cost_rule.game_cost
                else:
                    cost = 0
            else:
                cost = 0

            if player_total_games <= self.cost_rule.free_games + self.cost_rule.half_cost_games:
                cost /= 2

            transactions.append(Transaction(game.starttime, cost, game.get_pool_display() + " game attendance"))

        # create transactions for other charges
        for other in OtherCharge.objects.filter(player=self.player, time__range=QuarterDatetimeRange(self.quarter)):
            transactions.append(Transaction(other.time, other.amount, other.remarks))

        # create transactions for payments
        for payment in Payment.objects.filter(player=self.player, time__range=QuarterDatetimeRange(self.quarter)):
            transactions.append(Transaction(payment.time, -payment.amount, \
                                            payment.get_payment_type_display() + ' payment: ' + payment.reference))

        balance = self.start_balance
        sorted_transactions = sorted(transactions, key=attrgetter('dt'))
        for tr in sorted_transactions:
            balance += tr.amount
            tr.balance = balance

        return sorted_transactions

    def QuarterStartDatetime(self):
        return QuarterStartDatetime(self.quarter)
    
    def QuarterStartDate(self):
        return QuarterStartDatetime(self.quarter).date()

    def quarter_start_date(self):
        return self.QuarterStartDate()
    quarter_start_date.short_description = 'Quarter Start Date'
    quarter_start_date.admin_oder_field = 'quarter'    

    def formatted_start_balance(self):
        return '${:>8.2f}'.format(self.start_balance)
    formatted_start_balance.short_description = 'Quarter Start Balance'
    formatted_start_balance.admin_oder_field = 'start_balance'

    def __str__(self):
        return 'PlayerQuarterCostRule for player ' + str(self.player) + \
          ' in quarter starting ' + QuarterStartDatetime(self.quarter).isoformat() + ' is ' + str(self.cost_rule) + \
          ' with a prorate of ' + str(self.prorate)

        

class Payment(models.Model):
    CHECK = 1
    PAYPAL = 2
    TO_CHRIS = 3
    CASH = 4
    ACCOUNT_CREDIT = 5
    PAYMENT_TYPE_CHOICES = (
        (CHECK, 'check'),
        (PAYPAL, 'PayPal'),
        (TO_CHRIS, 'to Chris'),
        (CASH, 'cash'),
        (ACCOUNT_CREDIT, 'account credit'),
    )
    player = models.ForeignKey(Player)
    time = models.DateTimeField()
    amount = models.FloatField(default=0.0)
    payment_type = models.PositiveSmallIntegerField(choices=PAYMENT_TYPE_CHOICES, default=CASH)
    reference = models.CharField(blank=True, max_length=200)

    def QuarterID(self):
        return QuarterID(self.time)

    def QuarterStartDatetime(self):
        return QuarterStartDatetime(self.QuarterID())
    
    def QuarterStartDate(self):
        return QuarterStartDatetime(self.QuarterID()).date()

    def formatted_amount(self):
        return '${:>8.2f}'.format(self.amount)
    formatted_amount.short_description = 'Payment Amount'
    formatted_amount.admin_oder_field = 'amount'
    
    def __str__(self):
        return self.get_payment_type_display() + ' payment of ' + str(self.amount) + ' on ' + \
          timezone.localtime(self.time).ctime() + ' for player ' + str(self.player)


class OtherCharge(models.Model):
    player = models.ForeignKey(Player)
    time = models.DateTimeField()
    amount = models.FloatField(default=0.0)
    remarks = models.CharField(blank=True, max_length=200)

    def QuarterID(self):
        return QuarterID(self.time)

    def QuarterStartDatetime(self):
        return QuarterStartDatetime(self.QuarterID())
    
    def QuarterStartDate(self):
        return QuarterStartDatetime(self.QuarterID()).date()
    
    def formatted_amount(self):
        return '${:>8.2f}'.format(self.amount)
    formatted_amount.short_description = 'Payment Amount'
    formatted_amount.admin_oder_field = 'amount'
    
    def __str__(self):
        return 'Charge of ' + str(self.amount) + ' on ' + timezone.localtime(self.time).ctime() + \
          ' for player ' + str(self.player) + ' for ' + str(self.remarks)
