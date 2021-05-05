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
import json

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
	clearing_price = models.FloatField(initial=0)
	clearing_rate = models.FloatField(initial=0)

	def buys(self):
		buys_list = []
		buys = Order.filter(group=self,direction='buy',status='active')
		for buy in buys:
			buys_list.append({
				'p_low': buy.p_low,
				'p_high': buy.p_high,
				'q_max': buy.q_max,
				'u_max': buy.u_max,
				'direction': buy.direction,
				'status': buy.status,
				'timestamp':buy.timestamp
			})
		return buys_list

	def sells(self):
		sells_list = []
		sells = Order.filter(group=self,direction='sell',status='active')
		for sell in sells:
			sells_list.append({
				'p_low': sell.p_low,
				'p_high': sell.p_high,
				'q_max': sell.q_max,
				'u_max': sell.u_max,
				'direction': sell.direction,
				'status': sell.status,
				'timestamp':sell.timestamp
			})
		return sells_list

class Player(BasePlayer):
	cash = models.FloatField(initial=5000)
	inventory = models.FloatField(initial=500)
	num_buys = models.IntegerField(initial=0)
	num_sells = models.IntegerField(initial=0)
	# Current order states
	direction = models.StringField() # 'buy', 'sell'
	q_max = models.IntegerField()
	u_max = models.FloatField()
	p_low = models.FloatField()
	p_high = models.FloatField()
	status = models.StringField() #

	def live_method(self, data):
		self.new_order(data)

		if(data['direction'] == 'buy'):
			return_data = {'type': 'buy', 'bids_or_asks': self.group.buys()}
		elif (data['direction'] == 'sell'):
			return_data = {'type': 'sell', 'bids_or_asks': self.group.sells()}
		return {0: return_data}

	def new_order(self, order):
		self.direction = order['direction']
		self.q_max = order['q_max']
		self.u_max = order['u_max']
		self.p_low = order['p_low']
		self.p_high = order['p_high']
		self.status = order['status']

		if order['direction'] == 'buy':
			self.num_buys += 1
		if order['direction'] == 'sell':
			self.num_sells += 1

		Order.create(player=self,
					group = self.group,
					timestamp = order['timestamp'],
					direction = order['direction'],
					q_max = order['q_max'],
					u_max = order['u_max'],
					p_low = order['p_low'],
					p_high = order['p_high'],
					status = order['status'])
		#print(self.orders())

	# might need to use Order.objects in older otree versions
	def orders(self):
		order_list = []
		orders = Order.filter(player=self,direction='buy',status='active')
		for order in orders:
			order_list.append({
				'p_low': order.p_low,
				'p_high': order.p_high,
				'q_max': order.q_max,
				'u_max': order.u_max,
				'direction': order.direction,
				'status': order.status,
				'timestamp':order.timestamp
			})
		return order_list

	def buys(self):
		buys_list = []
		buys = Order.filter(player=self,direction='buy',status='active')
		for buy in buys:
			buys_list.append({
				'p_low': buy.p_low,
				'p_high': buy.p_high,
				'q_max': buy.q_max,
				'u_max': buy.u_max,
				'direction': buy.direction,
				'status': buy.status,
				'timestamp':buy.timestamp
			})
		return buys_list

	def sells(self):
		sells_list = []
		sells = Order.filter(player=self,direction='sell',status='active')
		for sell in sells:
			sells_list.append({
				'p_low': sell.p_low,
				'p_high': sell.p_high,
				'q_max': sell.q_max,
				'u_max': sell.u_max,
				'direction': sell.direction,
				'status': sell.status,
				'timestamp':sell.timestamp
			})
		return sells_list

class Order(ExtraModel):
	player = models.Link(Player)
	group = models.Link(Group)
	timestamp = models.FloatField()
	direction = models.StringField() # 'buy', 'sell'
	q_max = models.IntegerField()
	u_max = models.FloatField()
	p_low = models.FloatField()
	p_high = models.FloatField()
	status = models.StringField()