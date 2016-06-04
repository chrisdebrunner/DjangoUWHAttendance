from django.db import models
import datetime

# Create your models here.

class Player(models.Model):
    firstname = models.CharField(max_length=40)
    lastname = models.CharField(max_length=40)
    initial_num_games = models.IntegerField(default=0)
    initial_balance = models.FloatField(default=0)
    email = models.EmailField(blank=True, default='')
    notes = models.CharField(blank=True, max_length=100)
    
    def __str__(self):
        return self.firstname + ' ' + self.lastname


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
    
    def __str__(self):
        return 'game on ' + str(self.starttime)


class CostRule(models.Model):
    REGULAR = 1
    VISITOR = 2
    JUNIOR = 3
    BEGINNER = 4
    PLAYER_CLASS_CHOICES = (
        (REGULAR, 'player'),
        (VISITOR, 'visitor'),
        (JUNIOR, 'junior player'),
        (BEGINNER, 'beginner player'),
    )
    GAMES_PER_WEEK_CHOICES = (
        (0, 'no quarterly'),
        (1, 'one game per week quarterly'),
        (2, 'two games per week quarterly'),
        (3, 'three games per week quarterly'),
        (4, 'four games per week quarterly'),
    )
    student = models.BooleanField(default=False)
    player_class = models.PositiveSmallIntegerField(choices=PLAYER_CLASS_CHOICES, default=REGULAR)
    quarterly_games_per_week = models.PositiveSmallIntegerField(choices=GAMES_PER_WEEK_CHOICES, default=0)
    game_cost = models.FloatField()
    quarter_cost = models.FloatField()
    free_games = models.SmallIntegerField()
    half_cost_games = models.SmallIntegerField()
    
    def __str__(self):
        if self.student:
            student_string = 'student '
        else:
            student_string = ''
            
        return student_string + self.get_player_class_display() + ' '\
                + self.get_quarterly_games_per_week_display()

    
    
class PlayerQuarterCostRule(models.Model):
    cost_rule = models.ForeignKey(CostRule)
    player = models.ForeignKey(Player)
    quarter = models.PositiveSmallIntegerField()
    prorate = models.FloatField(default=1.0)
    
    class Meta:
        unique_together = ("player", "quarter")

    def QuarterStartDate(self, id):
        return datetime.date(2000 + ((id-1) // 4), 3 * ((id-1) % 4) + 1, 1)

    def QuarterID(self, dt):
        return 4 * (dt.year - 2000) + ((dt.month-1) // 3) + 1

    def __str__(self):
        return 'PlayerQuarterCostRule for player ' + str(self.player) + \
          ' in quarter starting ' + self.QuarterStartDate(self.quarter).isoformat() + ' is ' + str(self.cost_rule) + \
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
    amount = models.FloatField()
    payment_type = models.PositiveSmallIntegerField(choices=PAYMENT_TYPE_CHOICES, default=CASH)
    reference = models.CharField(blank=True, max_length=200)

    def __str__(self):
        return self.get_payment_type_display() + ' payment of ' + str(self.amount) + ' on ' + \
          str(self.time) + ' for player ' + str(self.player)


class OtherCharge(models.Model):
    player = models.ForeignKey(Player)
    time = models.DateTimeField()
    amount = models.FloatField()
    remarks = models.CharField(blank=True, max_length=200)

    def __str__(self):
        return 'Charge of ' + str(self.amount) + ' on ' + str(self.time) + ' for player ' + str(self.player) + \
                 ' for ' + str(self.remarks)
