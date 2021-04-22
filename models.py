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
        print(data)
        player = self.get_player_by_id(id_in_group)
        player.new_order(data)

        print(data)
        return {id_in_group: "Success"}


class Player(BasePlayer):
    cash = models.FloatField()
    inventory = models.FloatField()
    num_buys = models.IntegerField(initial=0)
    num_sells = models.IntegerField(initial=0)
    # Current order states
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

        if order['direction'] == 'buy':
            self.num_buys += 1
        if order['direction'] == 'sell':
            self.num_sells += 1

        Order.objects.create(player=self,
                    group = self.group,
                    timestamp = order['timestamp'],
                    direction = order['direction'],
                    max_quantity = order['max_quantity'],
                    max_rate = order['max_rate'],
                    p_min = order['p_min'],
                    p_max = order['p_max'],
                    status = order['status'])
        
        print(self.orders())
    
    def orders(self):
        return Order.objects.filter(player=self)
    
    def buys(self):
        return Order.objects.filter(player=self,direction='buy')
    
    def sells(self):
        return Order.objects.filter(player=self,direction='sell')



class Order(ExtraModel):
    player = models.Link(Player)
    group = models.Link(Group)
    timestamp = models.FloatField()
    direction = models.StringField() # 'buy', 'sell'
    max_quantity = models.IntegerField()
    max_rate = models.FloatField()
    p_min = models.FloatField()
    p_max = models.FloatField()
    status = models.StringField() # 