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
    EPIC = 3
    POOL_CHOICES = (
        (CARMODY, 'Carmody'),
        (VMAC, 'VMAC'),
        (EPIC, 'EPIC'),
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
        (5, 'five games per week quarterly'),
    )
    player_class = models.PositiveSmallIntegerField(choices=PLAYER_CLASS_CHOICES, default=REGULAR)
    is_visitor = models.BooleanField(default=False)
    quarterly_games_per_week = models.PositiveSmallIntegerField(choices=GAMES_PER_WEEK_CHOICES, default=0)
    game_cost = models.FloatField(default=0.0)
    quarter_cost = models.FloatField(default=0.0)
    covered_games_per_quarter = models.SmallIntegerField(default=0)
    free_games = models.SmallIntegerField(default=0)
    half_cost_games = models.SmallIntegerField(default=0)
    # note that the following field value defines disjoint sets of CostRules, and for a given quarter, only the CostRules in a given set
    # are valid
    first_valid_quarter = models.PositiveSmallIntegerField(default=0)        # the first quarter in which this cost rule is valid
    is_default = models.BooleanField(default=False)                          # default for all the rules expiring in a given quarter
    
    class Meta:
        unique_together = ("player_class", "is_visitor", "quarterly_games_per_week", "first_valid_quarter")

    def formatted_game_cost(self):
        return '${:>8.2f}'.format(self.game_cost)
    formatted_game_cost.short_description = 'Game Cost'
    formatted_game_cost.admin_oder_field = 'game_cost'

    def formatted_quarter_cost(self):
        return '${:>8.2f}'.format(self.quarter_cost)
    formatted_quarter_cost.short_description = 'Quarter Cost'
    formatted_quarter_cost.admin_oder_field = 'quarter_cost'

    @staticmethod
    def FirstValidQuarterForQuarter(quarter):
        """return the first_valid_quarter value from CostRules that is the largest/latest <= to quarter"""
        return CostRule.objects.filter(first_valid_quarter__lte=quarter).aggregate(models.Max('first_valid_quarter'))['first_valid_quarter__max']


    def IsValidForQuarter(self, quarter):
        """return true if self is valid for this quarter (ie no other CostRule has 
        the same player, is_visitor, and quaterly_games_per_week and a larger first_valid_quarter)"""
        # find the largest/latest first_valid_quarter less than the current quarter
        # this CostRule is valid for this quarter if
        fvq4q = CostRule.FirstValidQuarterForQuarter(quarter)
        return self.first_valid_quarter == fvq4q

    @staticmethod
    def DefaultCostRule(quarter):
        """return the default cost rule for the quarter"""
        # find the largest/latest first_valid_quarter less than the current quarter
        fvq4q = CostRule.FirstValidQuarterForQuarter(quarter)
        # find the default cost rule for the largest/latest first_valid_quarter
        return CostRule.objects.get(is_default=True,first_valid_quarter=fvq4q)


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

    @classmethod
    def GetOrCreate(cls, player, quarter, cost_rule=None):
        """Get the PlayerQuarterCostRule for the given player and quarter, or Create a new PlayerQuarterCostRule with
        player, quarter, and cost_rule set as specified by the arguments. If cost_rule is not specified, check to see 
        if this player has a PlayerQuarterCostRule for an earlier quarter, and use its cost_rule, but only if it is 
        valid for the specified quarter. If there is no such PlayerQuarterCostRule or if the earlier cost rule is no 
        longer valid, use the default cost rule for the given quarter. If a new PlayerQuarterCostRule is created, it
        is saved.
        """
        pqcr = PlayerQuarterCostRule.objects.filter(player=player, quarter=quarter).first()
        if pqcr:
            return pqcr
        else:
            if cost_rule and cost_rule.IsValidForQuarter(quarter):
                new_cost_rule = cost_rule
            else:
                lastpqcr = PlayerQuarterCostRule.objects.filter(player=player,quarter__lt=quarter).order_by('quarter').last()
                if lastpqcr and lastpqcr.cost_rule.IsValidForQuarter(quarter):
                    new_cost_rule = lastpqcr.cost_rule
                else:
                    new_cost_rule = CostRule.DefaultCostRule(quarter)

            newpqcr = PlayerQuarterCostRule(player=player, quarter=quarter, cost_rule=new_cost_rule)
            newpqcr.save()
            newpqcr.Update()            # update the start_balance and start_num_games
            return newpqcr


    def Update(self, max_lookback=1):
        "Update start_balance and start_num_games based on max_lookback earlier quarters' info, transactions, and game counts"

        pqcrs = PlayerQuarterCostRule.objects.filter(player=self.player, quarter__lte=self.quarter).order_by('quarter')

        # note that pqcrs includes self (which we want to update) at the end
        PlayerQuarterCostRule.UpdatePlayerQuarterCostRules(pqcrs[max(0,len(pqcrs) - max_lookback - 1):])

    @staticmethod
    def UpdatePlayerQuarterCostRules(pqcrs):
        # Update start_balance and start_num_games for an iterable of PlayerQuarterCostRules
        # pqcrs is assumed to be in increasing quarter order without missing quarters, and to be all from a single player

        length = len(pqcrs)

        if length > 0:
            player = pqcrs[0].player

            # if the first PQCR in the iterable is the first in the database, make sure it is initialized
            # to the player's start balance and num games. Otherwise assume its start_balance and start_num_games
            # are set correctly
            if pqcrs[0] == PlayerQuarterCostRule.objects.filter(player=player).order_by('quarter').first():
                pqcrs[0].start_balance = player.initial_balance
                pqcrs[0].start_num_games = player.initial_num_games
                pqcrs[0].save()

            if length > 1:
                balance = pqcrs[0].start_balance + sum(pqcrs[0].GetTransactions())
                num_games = pqcrs[0].start_num_games + pqcrs[0].player.game_set.filter(starttime__range=QuarterDatetimeRange(pqcrs[0].quarter)).count()

                for pqcr in pqcrs[1:]:
                    pqcr.start_balance = balance
                    pqcr.start_num_games = num_games
                    pqcr.save()

                    if pqcr != pqcrs[length-1]:
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

            description = "{:s} game attendance, game {:d} of {:d} in week {:d}".format(game.get_pool_display(), games_in_week, self.cost_rule.quarterly_games_per_week, game_week)
            transactions.append(Transaction(game.starttime, cost, description))

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
    DIRECT_DEPOSIT = 6
    PAYMENT_TYPE_CHOICES = (
        (CHECK, 'check'),
        (PAYPAL, 'PayPal'),
        (TO_CHRIS, 'to Chris'),
        (CASH, 'cash'),
        (ACCOUNT_CREDIT, 'account credit'),
        (DIRECT_DEPOSIT, 'direct deposit'),
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
