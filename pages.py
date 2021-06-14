from otree.api import Currency as c, currency_range
from ._builtin import Page, WaitPage
from .models import Constants
import csv

class DecisionWaitPage(WaitPage):
    body_text = 'Waiting for all players to be ready'
    wait_for_all_groups = True
    #after_all_players_arrive = 'schedule'

    def is_displayed(self):
        return True

class Decision(Page):
    #timeout_seconds = 180
    live_method = "live_method"

    def is_displayed(self):
        return True
    
    def vars_for_template(self):
        bet_file = self.group.bet_file()
        with open('flow_market/bets/' + bet_file) as f:
            rows = list(csv.DictReader(f))

        bets = []    
        for row in rows:
            if (int(row['trader_id']) == self.player.id_in_group):
                bets.append({
                    'direction': str(row['direction']),
                    'limit_price': int(row['limit_price']),
                    'quantity': int(row['quantity']),
                    'deadline': int(row['deadline'])
                })
        return {
            'bets': bets
        }


class ResultsWaitPage(WaitPage):
    body_text = 'Waiting for all players to be ready'
    wait_for_all_groups = True


class Results(Page):
    def is_displayed(self):
        return True
    
    


page_sequence = [DecisionWaitPage, Decision, ResultsWaitPage, Results]
