from otree.api import (
    models,
    BaseConstants,
    BaseSubsession,
    BaseGroup,
    BasePlayer,
    ExtraModel,
)
from otree import live
from .delayedFunct import call_with_delay
from jsonfield import JSONField

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
		#for g in self.get_groups():
		#	g.init_copies()
		#	print(g.order_copies)

def init_copies():
	return {1: {}, 2: {}, 3: {}, 4: {}}

class Group(BaseGroup):
	# order_copies[player_id_in_group][order_id]
	order_copies = JSONField(null=True, default=init_copies)

	
	def new_order(self, order,playerID, currentID):
		print(self.order_copies)
		cache = self.order_copies
		cache[str(playerID)][str(currentID)] = {
				'player': playerID,
				'p_min': order['p_min'],
				'p_max': order['p_max'],
				'q_max': order['q_max'],
				'u_max': order['u_max'],
				'direction': order['direction'],
				'status': order['status'],
				'orderID':currentID
			}
		self.order_copies = cache
		self.save()

	def buys(self):
		buys_list = []
		for p in self.get_players():
			for value in self.order_copies[str(p.id_in_group)].values():
				if value['direction'] == 'buy' and value['status'] == 'active':
					buys_list.append(value)
		return buys_list

	def sells(self):
		sells_list = []
		for p in self.get_players():
			for value in self.order_copies[str(p.id_in_group)].values():
				if value['direction'] == 'sell' and value['status'] == 'active':
					sells_list.append(value)
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
		payloads = {}
		if len(buys) > 0 and len(sells) > 0:
			#Calculate the clearing price
			clearing_price = self.clearingPrice(buys, sells)
			print("Clearing Price: " + str(clearing_price))
			#Graph the clearing price
			
			for player in self.get_players():
				payloads[player.participant.code] = {"type": 'clearing_price', "clearing_price": clearing_price, "buys": buys, "sells": sells}
			
			live._live_send_back(self.get_players()[0].participant._session_code, self.get_players()[0].participant._index_in_pages, payloads)

			#Update the traders' profits and orders
			print("----Sells in Update--------------------")
			for sell in sells:
				seller = self.get_player_by_id(sell['player'])
				print(self.order_copies[str(seller.id_in_group)][str(sell['orderID'])])
				trader_vol = self.calcSupply(sell, clearing_price)
				sell['q_max'] -= trader_vol
				cache = self.order_copies
				cache[str(seller.id_in_group)][str(sell['orderID'])]['q_max'] -= trader_vol
				self.order_copies = cache
				self.save()

				
				# remove the order if q_max <= 0
				if sell['q_max'] <= 0.0:
					cache = self.order_copies
					cache[str(seller.id_in_group)][str(sell['orderID'])]['status'] = 'expired'
					self.order_copies = cache
					self.save()
					sell['status'] = 'expired'
					#ReGraph KLF market since order expired
					for player in self.get_players():
						payloads[player.participant.code] = {"type": 'regraph', "buys": buys, "sells": sells}
					
					live._live_send_back(self.get_players()[0].participant._session_code, self.get_players()[0].participant._index_in_pages, payloads)


				seller.updateProfit(trader_vol * clearing_price)
				seller.updateVolume(-trader_vol)
				print("Trader " + str(sell['player']) + " Cash: " + str(seller.cash))
				print("Trader " + str(sell['player']) + " Inventory: " + str(seller.inventory))
				# Use live send back to update seller's frontend
				for player in self.get_players():
					payloads[player.participant.code] = {"type": 'none'}
				
				payloads[seller.participant.code] = {"type": 'update', "cash": seller.cash, "inventory": seller.inventory}
				
				live._live_send_back(self.get_players()[0].participant._session_code, self.get_players()[0].participant._index_in_pages, payloads)

			print("----Buys in Update--------------------")
			for buy in buys:
				buyer = self.get_player_by_id(buy['player'])
				print(self.order_copies[str(buy['player'])][str(buy['orderID'])])
				trader_vol = self.calcDemand(buy, clearing_price)
				buy['q_max'] -= trader_vol
				cache = self.order_copies
				cache[str(buy['player'])][str(buy['orderID'])]['q_max'] -= trader_vol
				self.order_copies = cache
				self.save()

				#remove the order if q_max <= 0
				if (buy['q_max'] <= 0.0):
					cache = self.order_copies
					cache[str(buy['player'])][str(buy['orderID'])]['status'] = 'expired'
					self.order_copies = cache
					self.save()
					buy['status'] = 'expired'
					# ReGraph KLF market since order expired
					for player in self.get_players():
						payloads[player.participant.code] = {"type": 'regraph', "buys": buys, "sells": sells}
					
					live._live_send_back(self.get_players()[0].participant._session_code, self.get_players()[0].participant._index_in_pages, payloads)

				buyer.updateProfit(trader_vol * clearing_price)
				buyer.updateVolume(-trader_vol)
				print("Trader " + str(buy['player']) + " Cash: " + str(buyer.cash))
				print("Trader " + str(buy['player']) +" Inventory: " + str(buyer.inventory))
				# Use live send back to update buyer's frontend
				for player in self.get_players():
					payloads[player.participant.code] = {"type": 'none'}
				
				payloads[buyer.participant.code] = {"type": 'update', "cash": buyer.cash, "inventory": buyer.inventory}
				
				live._live_send_back(self.get_players()[0].participant._session_code, self.get_players()[0].participant._index_in_pages, payloads)
		else:
			#Clear the clearing price graph
			for player in self.get_players():
				payloads[player.participant.code] = {"type": 'clear'}
			
			live._live_send_back(self.get_players()[0].participant._session_code, self.get_players()[0].participant._index_in_pages, payloads)

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
	status = models.StringField()
	updateRunning = models.BooleanField(initial=False)

	currentID = models.IntegerField(initial=0)

	def setUpdateRunning(self):
		self.updateRunning = True

	def live_method(self, data):
		self.new_order(data)

		if not self.updateRunning:
			for p in self.group.get_players():
				p.setUpdateRunning()
			call_with_delay(2, self.group.update)	

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

		Order.objects.create(player=self,
					group = self.group,
					orderID = self.currentID,
					direction = order['direction'],
					q_max = order['q_max'],
					u_max = order['u_max'],
					p_min = order['p_min'],
					p_max = order['p_max'],
					status = order['status'])
		
		self.group.new_order(order, self.id_in_group, self.currentID)
		
		self.currentID += 1
	
	def updateProfit(self, profit):
		self.cash += profit
	
	def updateVolume(self, volume):
		self.inventory += volume

class Order(ExtraModel):
	player = models.Link(Player)
	group = models.Link(Group)
	orderID = models.IntegerField()
	direction = models.StringField() # 'buy', 'sell'
	q_max = models.FloatField()
	u_max = models.FloatField()
	p_min = models.FloatField()
	p_max = models.FloatField()
	status = models.StringField()