from otree.api import Currency as c, currency_range  # type: ignore
from ._builtin import Page, WaitPage
from .models import Constants, Group
import csv


class DecisionWaitPage(WaitPage):
    body_text = 'Waiting for all players to be ready'
    wait_for_all_groups = True
    #after_all_players_arrive = 'schedule'

    def is_displayed(self):
        return True


class Decision(Page):
    #timeout_seconds = self.group.round_length()
    live_method = "live_method"

    def is_displayed(self):
        return True

    def vars_for_template(self):
        bet_file = self.group.bet_file()
        with open('flow_market/bets/' + bet_file) as f:
            rows = list(csv.DictReader(f))

        bets = []
        rowNum = 0
        for row in rows:
            if (int(row['trader_id']) == self.player.id_in_group):
                bets.append({
                    'direction': str(row['direction']).upper(),
                    'limit_price': int(row['limit_price']),
                    'quantity': int(row['quantity']),
                    'deadline': int(row['deadline']),
                    'bet_id': self.group.get_bet_id(rowNum),
                })
            rowNum += 1
        # print("sending bets", bets)
        return {
            'bets': bets,
            'treatment': self.group.treatment(),
            'max_price': self.group.max_price(),
            'max_u_max': self.group.max_u_max(),
            'max_q_max': self.group.max_q_max(),
            'min_price_delta': self.group.min_price_delta(),
            'update_freq': self.group.update_freq(),
            "disable_algo_flo": 'true',
        }


class ResultsWaitPage(WaitPage):
    body_text = 'Waiting for all players to be ready'
    wait_for_all_groups = True


class Results(Page):
    def is_displayed(self):
        return True


page_sequence = [DecisionWaitPage, Decision, ResultsWaitPage, Results]
