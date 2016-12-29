from django import forms
from .models import CostRule, Player, PlayerQuarterCostRule, QuarterWeekNumber
from django.utils.translation import ugettext as _
from django.utils import timezone
from datetime import datetime
from django.http import QueryDict


class CostRuleSelectForm(forms.Form):
    player_class = forms.ChoiceField(choices=CostRule.PLAYER_CLASS_CHOICES,
                                     widget=forms.Select(attrs={'onchange': 'submit()'}),
                                     label='Player category')
    is_visitor = forms.BooleanField(required=False,
                                    widget=forms.CheckboxInput(attrs={'onchange': 'submit()'}),
                                    label='Visitor?')
    games_per_week = forms.ChoiceField(choices=CostRule.GAMES_PER_WEEK_CHOICES,
                                       widget=forms.Select(attrs={'onchange': 'submit()'}),
                                       label='Quarterly games per week')

    def __init__(self, transactions_view, *args, **kwargs):
        super(CostRuleSelectForm, self).__init__(*args, **kwargs)
        if not transactions_view.user.is_staff:
            self.full_clean()               # clean before disabling fields since disabled fields ignore new values
            self.fields['player_class'].disabled = True
            self.fields['is_visitor'].disabled = True
            quarter_week_number = QuarterWeekNumber(transactions_view.object.quarter, datetime.now(tz=timezone.get_current_timezone()))
            self.fields['games_per_week'].disabled = not (0 < quarter_week_number <= 4)

    @staticmethod
    def InitFromCostRule(cr):
        return {'player_class': str(cr.player_class),
                'is_visitor': cr.is_visitor,
                'games_per_week': str(cr.quarterly_games_per_week)}

    def clean(self):
        cleaned_data = super(CostRuleSelectForm, self).clean()
        player_class = cleaned_data.get('player_class')
        is_visitor = cleaned_data.get('is_visitor')
        games_per_week = cleaned_data.get('games_per_week')

        try:
            cr = CostRule.objects.get(player_class=player_class,
                                      is_visitor=is_visitor,
                                      quarterly_games_per_week=games_per_week)
            self.cost_rule = cr
            return self.cleaned_data
        except CostRule.DoesNotExist:
            raise forms.ValidationError(_("%(player_class)s%(is_visitor)s with %(games_per_week)s games per week is not a valid cost rule") %
                                        {'player_class': dict(CostRule.PLAYER_CLASS_CHOICES).get(int(player_class)), 'is_visitor': (' visitor' if is_visitor else ''), 'games_per_week': games_per_week})


class PlayerQuarterCostRuleChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, pqcr):
        return 'Quarter starting ' + pqcr.QuarterStartDate().isoformat()

class QuarterSelectForm(forms.Form):
    player_quarter_cost_rule = PlayerQuarterCostRuleChoiceField(queryset=PlayerQuarterCostRule.objects.none(),
                                                                empty_label=None,
                                                                widget=forms.Select(attrs={'onchange': 'submit()'}),
                                                                label='Quarter')

    def __init__(self, transactions_view, *args, **kwargs):
        super(QuarterSelectForm, self).__init__(*args, **kwargs)
        
        self.fields['player_quarter_cost_rule'].queryset = PlayerQuarterCostRule.objects.filter(player=transactions_view.player).order_by('-quarter')


class PlayerSelectForm(forms.Form):
    player = forms.ModelChoiceField(queryset=Player.objects.all().order_by('user__last_name', 'user__first_name'),
                                    widget=forms.Select(attrs={'onchange': 'submit()'}))

    def __init__(self, transactions_view, *args, **kwargs):
        super(PlayerSelectForm, self).__init__(*args, **kwargs)
        
        if not transactions_view.user.is_staff:
            self.fields['player'].queryset = Player.objects.filter(user=transactions_view.user)
            self.full_clean()          # clean before disabling fields since disabled fields ignore new values
            self.fields['player'].disabled = True


