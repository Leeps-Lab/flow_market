from otree.api import (
    models,
    widgets,
    BaseConstants,
    BaseSubsession,
    BaseGroup,
    BasePlayer,
    Currency as c,
    currency_range,
)


author = 'LeepsLab'

doc = """
This is a continuous flow market game
"""


class Constants(BaseConstants):
    name_in_url = 'flow_market'
    players_per_group = 4
    num_rounds = 1


class Subsession(BaseSubsession):
    def creating_session(self):
        self.group_randomly()


class Group(BaseGroup):
    def live_method(self, id_in_group, data):
        payload = {
            
        }
        return {id_in_group: payload}


class Player(BasePlayer):
    pass

class Order(ExtraModel):
    player = models.Link(Player)
    group = models.Link(Group)