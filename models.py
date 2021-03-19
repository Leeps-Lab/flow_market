from otree.api import (
    models,
    widgets,
    BaseConstants,
    BaseSubsession,
    BaseGroup,
    BasePlayer,
    Currency as c,
    currency_range,
    ExtraModel
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
        player = self.get_player_by_id(id_in_group)
        player.set_order(data)

        payload = {

        }
        return {id_in_group: payload}


class Player(BasePlayer):
    # Order states
    direction = models.StringField() # 'buy', 'sell'
    max_quantity = models.IntegerField()
    max_rate = models.FloatField()
    p_min = models.FloatField()
    p_max = models.FloatField()
    status = models.StringField() # 

    def new_order(self, order):
        self.direction = order['direction']
        self.max_quantity = order['max_quantity']
        self.max_rate = order['max_rate']
        self.p_min = order['p_min']
        self.p_max = order['p_max']
        self.status = order['status']

        Order.create(player=self,
                    group = self.group,
                    order_timestamp = order['timestamp'],
                    direction = order['direction'],
                    max_quantity = order['max_quantity'],
                    max_rate = order['max_rate'],
                    p_min = order['p_min'],
                    p_max = order['p_max'],
                    status = order['status'])
    
    def order_book(self):
        return Order.filter(player=self)


class Order(ExtraModel):
    player = models.Link(Player)
    group = models.Link(Group)
    order_timestamp = models.FloatField()
    direction = models.StringField() # 'buy', 'sell'
    max_quantity = models.IntegerField()
    max_rate = models.FloatField()
    p_min = models.FloatField()
    p_max = models.FloatField()
    status = models.StringField() # 