from otree.api import (
    models,
    widgets,
    BaseConstants,
    BaseSubsession,
    BaseGroup,
    BasePlayer,
    Currency as c,
    currency_range,
    ExtraModel,
)
from otree import live
import asyncio
import json
import time
import threading

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

	def schedule(self):
		print("calling")
		groups = self.get_groups()
		for group in groups:
			group.schedule()


class Group(BaseGroup):
	clearing_price = models.FloatField(initial=0)
	clearing_rate = models.FloatField(initial=0)

	def buys(self):
		buys_list = []
		buys = Order.filter(group=self,direction='buy',status='active')
		for buy in buys:
			buys_list.append({
				'player': buy.player.id_in_group,
				'p_min': buy.p_min,
				'p_max': buy.p_max,
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
				'player': sell.player.id_in_group,
				'p_min': sell.p_min,
				'p_max': sell.p_max,
				'q_max': sell.q_max,
				'u_max': sell.u_max,
				'direction': sell.direction,
				'status': sell.status,
				'timestamp':sell.timestamp
			})
		return sells_list

	def calcDemand(self, buy, price):
		if (price <= buy['p_min']):
			if (buy['q_max'] < buy['u_max']):
				# Don't trade more than q_max
				return buy['q_max']
			# Trade at max rate if p <= p_min
			return buy['u_max']
		elif (price > buy['p_max']):
			# Don't trade if price is higher than max willingness to buy
			return 0.0
		else:
			# The price fell p_min < price < p_max
			trade_vol = buy['u_max'] * ((buy['p_max'] - price) / (buy['p_max'] - buy['p_min']))
			if (trade_vol > buy['q_max']):
				# Saturate to q_max if trade_vol will exceed q_max
				return buy['q_max']
			return trade_vol

	def calcSupply(self, sell, price):
		if (price < sell['p_min']):
			# Don't trade if price is lower than min willingness to sell
			return 0.0
		elif (price >= sell['p_max']):
			if (sell['q_max'] < sell['u_max']):
				# Don't trade more than q_max 
				return sell['q_max']
			# Trade at max rate if p >= p_max
			return sell['u_max']
		else:
			# The price fell p_min < price < p_max
			trade_vol = sell['u_max'] + ((price - sell['p_max']) / (sell['p_max'] - sell['p_min'])) * sell['u_max']
			if (trade_vol > sell['q_max']):
				# Saturate to q_max if trade_vol will exceed q_max
				return sell['q_max']
			return trade_vol

	def clearingPrice(self, buys, sells):
		# Get lowest and highest prices in books
		left = 0.0
		right = 200.0
		curr_iter = 0
		MAX_ITERS = 1000
		while (left < right):
			curr_iter += 1
			# Find a midpoint with the correct price tick precision
			index = (left + right) / 2.0
			# Calculate the aggregate supply and demand at this price
			dem = 0.0
			sup = 0.0
			for sell in sells:	
				sup += self.calcSupply(sell, index)

			for buy in buys:
				dem += self.calcDemand(buy, index)

			if (dem > sup):  		
				# We are left of the crossing point
				left = index
			elif (dem < sup):	# sup > dem
				# We are right of the crossing point
				right = index
			else:
				print("Found cross: " + str(index))
				return index

			if (curr_iter == MAX_ITERS):
				print("Trouble finding cross in max iterations, got: " + str(index))
				return index

	def update(self):
		buys = self.buys()
		sells = self.sells()
		if len(buys) > 0 and len(sells) > 0:
			#Calculate the clearing price
			clearing_price = self.clearingPrice(buys, sells)
			print("Clearing Price: " + str(clearing_price))
			#Graph the clearing price
			#ReGraph KLF market since order expired

			#Update the traders' profits and orders
			for sell in sells:
				seller = self.get_player_by_id(sell['player'])
				sell_model_ref = Order.filter(player=seller,direction='sell',status='active',timestamp=sell['timestamp'])[0]
				trader_vol = self.calcSupply(sell, clearing_price)
				sell_model_ref.q_max -= trader_vol

				
				# remove the order if q_max <= 0
				if sell['q_max'] <= 0.0:
					sell_model_ref.status = 'expired'
					sell['status'] = 'expired'
					#ReGraph KLF market since order expired

				seller.updateProfit(trader_vol * clearing_price)
				seller.updateVolume(-trader_vol)
				print("Trader " + sell['player'] + " Cash: " + str(seller.cash))
				print("Trader " + sell['player'] + " Inventory: " + str(seller.inventory))
				# Use live send back to update seller's frontend

			for buy in buys:
				buyer = self.get_player_by_id(buy['player'])
				buy_model_ref = Order.filter(player=buyer,direction='buy',status='active',timestamp=buy['timestamp'])[0]
				trader_vol = self.calcDemand(buy, clearing_price)
				buy_model_ref.q_max -= trader_vol

				#remove the order if q_max <= 0
				if (buy['q_max'] <= 0.0):
					buy_model_ref.status = 'expired'
					buy['status'] = 'expired'
					# ReGraph KLF market since order expired

				buyer.updateProfit(trader_vol * clearing_price)
				buyer.updateVolume(-trader_vol)
				print("Trader " + buy['player'] + " Cash: " + str(buyer.cash))
				print("Trader " + buy['player'] +" Inventory: " + str(buyer.inventory))
				# Use live send back to update buyer's frontend
		else:
			#Clear the clearing price graph
			#live send
			return {'type': 'clear'}

class Player(BasePlayer):
	cash = models.FloatField(initial=5000)
	inventory = models.FloatField(initial=500)
	num_buys = models.IntegerField(initial=0)
	num_sells = models.IntegerField(initial=0)
	# Current order states
	direction = models.StringField() # 'buy', 'sell'
	q_max = models.IntegerField()
	u_max = models.FloatField()
	p_min = models.FloatField()
	p_max = models.FloatField()
	status = models.StringField() #

	def live_method(self, data):
		self.new_order(data)

		self.group.update()

		loop = asyncio.new_event_loop()
		task = loop.create_task(self.live_send())
		try:
			loop.run_until_complete(task)
		except asyncio.CancelledError:
			pass	

		#live._live_send_back(self.participant._session_code, self.participant._index_in_pages, {1: "hello world",2: "hello world",3: "hello world",4: "hello world"})

		if(data['direction'] == 'buy'):
			return_data = {'type': 'buy', 'buys': self.group.buys(), 'sells': self.group.sells()}
		elif (data['direction'] == 'sell'):
			return_data = {'type': 'sell', 'buys': self.group.buys(), 'sells': self.group.sells()}
		
		return {0: return_data}

	def new_order(self, order):
		self.direction = order['direction']
		self.q_max = order['q_max']
		self.u_max = order['u_max']
		self.p_min = order['p_min']
		self.p_max = order['p_max']
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
					p_min = order['p_min'],
					p_max = order['p_max'],
					status = order['status'])
		#print(self.orders())

	# might need to use Order.objects in older otree versions
	def orders(self):
		order_list = []
		orders = Order.filter(player=self,direction='buy',status='active')
		for order in orders:
			order_list.append({
				'player': order.player.id_in_group,
				'p_min': order.p_min,
				'p_max': order.p_max,
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
				'player': order.player.id_in_group,
				'p_min': buy.p_min,
				'p_max': buy.p_max,
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
				'player': order.player,
				'p_min': sell.p_min,
				'p_max': sell.p_max,
				'q_max': sell.q_max,
				'u_max': sell.u_max,
				'direction': sell.direction,
				'status': sell.status,
				'timestamp':sell.timestamp
			})
		return sells_list
	
	def updateProfit(self, profit):
		self.cash += profit
	
	def updateVolume(self, volume):
		self.inventory += volume

class Order(ExtraModel):
	player = models.Link(Player)
	group = models.Link(Group)
	timestamp = models.FloatField()
	direction = models.StringField() # 'buy', 'sell'
	q_max = models.IntegerField()
	u_max = models.FloatField()
	p_min = models.FloatField()
	p_max = models.FloatField()
	status = models.StringField()