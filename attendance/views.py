from django.shortcuts import get_object_or_404, render
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.views import generic

from .models import Game, Player

# Create your views here.

class IndexView(generic.ListView):
    template_name = 'attendance/index.html'
    context_object_name = 'latest_games_list'

    def get_queryset(self):
        """Return the last five games."""
        return Game.objects.order_by('-starttime')[:5]

class DetailView(generic.DetailView):
    model = Game
    template_name = 'attendance/detail.html'

class ResultsView(generic.DetailView):
    model = Game
    template_name = 'attendance/results.html'

def vote(request, game_id):
    game = get_object_or_404(Game, pk=game_id)
    post_choice = "not set"
    try:
        post_choice = request.POST['player']
        selected_choice = game.attendees.get(pk=post_choice)
    except (KeyError, Player.DoesNotExist):
        # Redisplay the game voting form.
        return render(request, 'attendance/detail.html', {
            'game': game,
            'error_message': "You didn't select a choice. Choice was: " + post_choice,
        })
    else:
        selected_choice.notes = 'hi there'
        selected_choice.save()
        # Always return an HttpResponseRedirect after successfully dealing
        # with POST data. This prevents data from being posted twice if a
        # user hits the Back button.
        return HttpResponseRedirect(reverse('attendance:results', args=(game.id,)))
