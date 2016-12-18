from django.http import Http404
from django.views import generic
from django.contrib.auth.mixins import LoginRequiredMixin
from .forms import CostRuleSelectForm, PlayerSelectForm, QuarterSelectForm
from .models import Player, PlayerQuarterCostRule, QuarterID, CostRule, QuarterWeekNumber

class TransactionsView(LoginRequiredMixin, generic.DetailView):
    model = PlayerQuarterCostRule
    template_name = 'attendance/transactions.html'
    login_url = '/attendance/login/'
    user = None
    player = None
    quarter_select_form = None
    object = None

    def dispatch(self, request, *args, **kwargs):
        self.user = request.user
        kwargs['has_permission'] = True               # put has_permission in context
        self.request = request
        return super(TransactionsView, self).dispatch(request, *args, **kwargs)

    def create_forms(self, request, request_dict, kwargs):
        if self.user.is_staff:
            psf = PlayerSelectForm(self, data=request_dict, initial={'player': request.session.get('player_pk')})
        else:
            psf_data = {'player': str(Player.objects.get(user=self.user).pk)}
            psf = PlayerSelectForm(self, data=psf_data, initial=psf_data)
            
        if psf.is_valid():
            self.player = psf.cleaned_data['player']
            request.session['player_pk'] = self.player.pk
            if psf.has_changed() or len(request_dict) == 0:
                qsf_data = {'player_quarter_cost_rule': PlayerQuarterCostRule.objects.filter(player=self.player).order_by('-quarter').first().pk}
                self.quarter_select_form = QuarterSelectForm(self, data=qsf_data, initial=qsf_data)
            else:
                self.quarter_select_form = QuarterSelectForm(self, data=request_dict, initial={'player_quarter_cost_rule': request.session.get('player_quarter_cost_rule_pk')})
                
            if self.quarter_select_form.is_valid():
                self.object = self.quarter_select_form.cleaned_data['player_quarter_cost_rule']
                request.session['player_quarter_cost_rule_pk'] = self.object.pk
                crsf_data = CostRuleSelectForm.InitFromCostRule(self.object.cost_rule)
                if self.quarter_select_form.has_changed():
                    crsf = CostRuleSelectForm(self, data=crsf_data, initial=crsf_data)
                else:
                    # make sure all fields are included in data, even those that are disabled
                    updated_crsf_data = crsf_data.copy()
                    updated_crsf_data.update({k: (v[0] if isinstance(v,list) else v) for k,v in request_dict.items()})
                    crsf = CostRuleSelectForm(self, data=updated_crsf_data, initial=crsf_data)
                    
                # update the selected PlayerQuarterCostRule cost rule if it has changed
                if crsf.is_valid() and crsf.has_changed():
                    self.object.cost_rule = crsf.cost_rule
                    self.object.save()
                    # also update subsequent quarters -- get latest quarter
                    self.object.Update(pqcrs=PlayerQuarterCostRule.objects.filter(player=self.object.player, quarter__gte=self.object.quarter).order_by('quarter'))

                kwargs['cost_rule_select_form'] = crsf

            else:
                self.object = None
                request.session['player_quarter_cost_rule_pk'] = ''
            
        else:
            request.session['player_pk'] = ''
            request.session['player_quarter_cost_rule_pk'] = ''

        kwargs['player_select_form'] = psf
        kwargs['quarter_select_form'] = self.quarter_select_form

        return kwargs
        

    def post(self, request, *args, **kwargs):

        newkwargs = self.create_forms(request, request.POST, kwargs)

        return self.render_to_response(self.get_context_data(**newkwargs))

    def get(self, request, *args, **kwargs):

        if 'player_pk' in request.session: del request.session['player_pk']
        if 'player_quarter_cost_rule_pk' in request.session: del request.session['player_quarter_cost_rule_pk']

        newkwargs = self.create_forms(request, {}, kwargs)
        
        return self.render_to_response(self.get_context_data(**newkwargs))
        


    # get_queryset should only return PlayerQuarterCostRules for the logged in user as identified in TransactionSelectForm
    def get_queryset(self):
        if self.quarter_select_form and self.quarter_select_form.is_valid():
            return self.quarter_select_form.fields['player_quarter_cost_rule'].queryset.all()
        else:
            return PlayerQuarterCostRule.objects.none()
        

    # override get_object to look for just pk or return none
    def get_object(self, queryset):
        return self.object
        

