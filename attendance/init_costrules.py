import os
import sys
os.environ['DJANGO_SETTINGS_MODULE'] = 'djangoUWH.settings'
sys.path.insert(0, '/Users/chd/Documents/UWH/WebSiteDesigns/django/djangoUWH')

import django
django.setup()

from attendance.models import Player, Game, CostRule, Quarter, PlayerQuarterCostRule

CostRule.objects.all().delete()

cr01 = CostRule(student=False, player_class=CostRule.BEGINNER, quarterly_games_per_week=0, game_cost=10.00, quarter_cost=  0.00, free_games=3, half_cost_games=13)
cr01.save()
cr02 = CostRule(student=False, player_class=CostRule.VISITOR,  quarterly_games_per_week=0, game_cost=10.00, quarter_cost=  0.00, free_games=0, half_cost_games=13)
cr02.save()
cr03 = CostRule(student=False, player_class=CostRule.JUNIOR,   quarterly_games_per_week=0, game_cost= 0.00, quarter_cost=  0.00, free_games=0, half_cost_games= 0)
cr03.save()
cr04 = CostRule(student=False, player_class=CostRule.REGULAR,  quarterly_games_per_week=0, game_cost=10.00, quarter_cost=  0.00, free_games=0, half_cost_games= 0)
cr04.save()
cr05 = CostRule(student=False, player_class=CostRule.REGULAR,  quarterly_games_per_week=1, game_cost=10.00, quarter_cost= 80.00, free_games=0, half_cost_games= 0)
cr05.save()
cr06 = CostRule(student=False, player_class=CostRule.REGULAR,  quarterly_games_per_week=2, game_cost=10.00, quarter_cost=150.00, free_games=0, half_cost_games= 0)
cr06.save()
cr07 = CostRule(student=False, player_class=CostRule.REGULAR,  quarterly_games_per_week=3, game_cost=10.00, quarter_cost=220.00, free_games=0, half_cost_games= 0)
cr07.save()
cr08 = CostRule(student=False, player_class=CostRule.REGULAR,  quarterly_games_per_week=4, game_cost=10.00, quarter_cost=290.00, free_games=0, half_cost_games= 0)
cr08.save()

cr09 = CostRule(student=True,  player_class=CostRule.VISITOR,  quarterly_games_per_week=0, game_cost= 6.00, quarter_cost=  0.00, free_games=0, half_cost_games=13)
cr09.save()
cr10 = CostRule(student=True,  player_class=CostRule.BEGINNER, quarterly_games_per_week=0, game_cost= 6.00, quarter_cost=  0.00, free_games=3, half_cost_games=13)
cr10.save()
cr11 = CostRule(student=True,  player_class=CostRule.REGULAR,  quarterly_games_per_week=0, game_cost= 6.00, quarter_cost=  0.00, free_games=0, half_cost_games= 0)
cr11.save()
cr12 = CostRule(student=True,  player_class=CostRule.REGULAR,  quarterly_games_per_week=1, game_cost= 6.00, quarter_cost= 50.00, free_games=0, half_cost_games= 0)
cr12.save()
cr13 = CostRule(student=True,  player_class=CostRule.REGULAR,  quarterly_games_per_week=2, game_cost= 6.00, quarter_cost= 90.00, free_games=0, half_cost_games= 0)
cr13.save()
cr14 = CostRule(student=True,  player_class=CostRule.REGULAR,  quarterly_games_per_week=3, game_cost= 6.00, quarter_cost=130.00, free_games=0, half_cost_games= 0)
cr14.save()
cr15 = CostRule(student=True,  player_class=CostRule.REGULAR,  quarterly_games_per_week=4, game_cost= 6.00, quarter_cost=170.00, free_games=0, half_cost_games= 0)
cr15.save()
