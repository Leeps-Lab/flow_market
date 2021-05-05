from otree.api import Currency as c, currency_range
from ._builtin import Page, WaitPage
from .models import Constants


class DecisionWaitPage(WaitPage):
    body_text = 'Waiting for all players to be ready'
    wait_for_all_groups = True
    #after_all_players_arrive = 

    def is_displayed(self):
        return True

class Decision(Page):
    live_method = "live_method"

    def is_displayed(self):
        return True


class ResultsWaitPage(WaitPage):
    body_text = 'Waiting for all players to be ready'
    wait_for_all_groups = True


class Results(Page):
    def is_displayed(self):
        return True


page_sequence = [DecisionWaitPage, Decision, ResultsWaitPage, Results]
