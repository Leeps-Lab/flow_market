# from otree.api import (  # type: ignore
#     models,
#     BaseConstants,
#     BaseSubsession,
#     BaseGroup,
#     BasePlayer,
#     ExtraModel,
# )
from otree.api import (  # type: ignore
    models,
    widgets,
    BaseConstants,
    BaseSubsession,
    BaseGroup,
    BasePlayer,
    ExtraModel,
    Currency as c,
    currency_range,
)
import csv
from otree import live  # type: ignore
from .delayedFunct import call_with_delay_infinite, call_with_delay
from jsonfield import JSONField
import time
import uuid

author = 'LeepsLab'

doc = """
This is a continuous flow market game
"""


class Constants(BaseConstants):
    name_in_url = 'flow_market'
    players_per_group = None
    num_rounds = 1

    index_template = 'flow_market/index.html'

    scripts_template = 'flow_market/scripts.html'
    scripts_init_graphs_template = 'flow_market/helperFuncs/init_graphs.html'
    scripts_init_sliders_template = 'flow_market/helperFuncs/init_sliders.html'
    scripts_imports_template = 'flow_market/helperFuncs/imports.html'
    scripts_InputDropdown_template = 'flow_market/helperFuncs/InputDropdown.html'
    scripts_constants_template = 'flow_market/helperFuncs/constants.html'

    style_template = 'flow_market/style.html'


def parse_config(config_file):
    with open('flow_market/configs/' + config_file) as f:
        rows = list(csv.DictReader(f))

    rounds = []
    for row in rows:
        rounds.append({
            'round': int(row['round']),
            'bet_file': str(row['bet_file']),
            'order_file': str(row['order_file']),
            'treatment': str(row['treatment']),
            'num_players': int(row['num_players']),
            'update_freq': float(row['update_freq']),
            'max_price': int(row['max_price']),
            'max_u_max': int(row['max_u_max']),
            'max_q_max': int(row['max_q_max']),
            'round_length': int(row['round_length']),
            'start_inv': int(row['start_inv']),
            'start_cash': int(row['start_cash'])
        })
    return rounds


class Subsession(BaseSubsession):
    def creating_session(self):
        # ENABLE
        # self.group_randomly()
        for p in self.get_players():
            p.init_cash_inv()


def init_copies():
    return {'1': {}, '2': {}, '3': {}, '4': {}}


class Group(BaseGroup):
    # order_copies[player_id_in_group][order_id]
    order_copies = JSONField(null=True, default=init_copies)

    def init_order_copies(self):
        self.order_copies = {str(i): {}
                             for i in range(1, self.num_players()+1)}

    def min_price_delta(self):
        return 0.1

    # was going to map uuid to row number of individual bet, but realized row number is unique itself
    def get_bet_id(self, rowNum):
        return rowNum

    def start_inv(self):
        return parse_config(self.session.config['config_file'])[self.round_number-1]['start_inv']

    def start_cash(self):
        return parse_config(self.session.config['config_file'])[self.round_number-1]['start_cash']

    def treatment(self):
        return parse_config(self.session.config['config_file'])[self.round_number-1]['treatment']

    def round_length(self):
        return parse_config(self.session.config['config_file'])[self.round_number-1]['round_length']

    def update_freq(self):
        return parse_config(self.session.config['config_file'])[self.round_number-1]['update_freq']

    def max_price(self):
        return parse_config(self.session.config['config_file'])[self.round_number-1]['max_price']

    def max_u_max(self):
        return parse_config(self.session.config['config_file'])[self.round_number-1]['max_u_max']

    def max_q_max(self):
        return parse_config(self.session.config['config_file'])[self.round_number-1]['max_q_max']

    def bet_file(self):
        return parse_config(self.session.config['config_file'])[self.round_number-1]['bet_file']

    def order_file(self):
        return parse_config(self.session.config['config_file'])[self.round_number-1]['order_file']

    def num_players(self):
        return parse_config(self.session.config['config_file'])[self.round_number-1]['num_players']

    def new_buy_algo(self, data):
        time_start = time.time()
        payloads = {}
        while time.time() < time_start + data['expiration_time']:
            # create group of orders
            for i in range(data['quantity_per']):
                self.get_player_by_id(data['trader_id']).new_order({
                    'p_min': data['p_min'],
                    'p_max': data['p_max'],
                    'q_max': data['q_max'],
                    'u_max': data['u_max'],
                    'direction': 'buy',
                    'status': 'active',
                    'timestamp': data['timestamp']
                })
            # Send out updated orderbooks to update graph on frontend
            # CONT see if we can get orderID into payload here
            for player in self.get_players():
                payloads[player.participant.code] = {
                    'type': 'buy', 'buys test': self.buys(), 'sells': self.sells()}
            print("Sending orderbooks")
            live._live_send_back(self.get_players()[0].participant._session_code, self.get_players()[
                                 0].participant._index_in_pages, payloads)
            # time between groups of orders
            time.sleep(2)

    def new_sell_algo(self, data):
        time_start = time.time()
        payloads = {}
        while time.time() < time_start + data['expiration_time']:
            # Create group of orders
            for i in range(data['quantity_per']):
                self.get_player_by_id(data['trader_id']).new_order({
                    'p_min': data['p_min'],
                    'p_max': data['p_max'],
                    'q_max': data['q_max'],
                    'u_max': data['u_max'],
                    'direction': 'sell',
                    'status': 'active',
                    'timestamp': data['timestamp']
                })
            # Send out updated orderbooks to update graph on frontend
            # CONT see if we can get orderID into payload here
            for player in self.get_players():
                payloads[player.participant.code] = {
                    'type': 'sell', 'buys': self.buys(), 'sells': self.sells()}
            live._live_send_back(self.get_players()[0].participant._session_code, self.get_players()[
                                 0].participant._index_in_pages, payloads)
            # time between groups of orders
            time.sleep(2)

    def set_bets(self):
        print("setting up bets")
        bet_file = self.bet_file()
        with open('flow_market/bets/' + bet_file) as f:
            rows = list(csv.DictReader(f))

        rowNum = 0
        for row in rows:
            data = {
                'trader_id': int(row['trader_id']),
                'direction': str(row['direction']),
                'limit_price': int(row['limit_price']),
                'quantity': int(row['quantity']),
                'deadline': int(row['deadline']),
                'bet_id': self.get_bet_id(rowNum),
            }
            call_with_delay((int(row['deadline'])/1000),
                            self.execute_bet, data)
            rowNum += 1
        return

    # seems to be updating price and inv correctly here for executing bets
    # HERE works execute_bet
    def execute_bet(self, data):
        print("executing bet:", data)
        player = self.get_player_by_id(data['trader_id'])
        if data['direction'] == 'buy':
            player.updateProfit(data['quantity']*data['limit_price'])
            player.updateVolume(-data['quantity'])
        else:
            player.updateProfit(-data['quantity']*data['limit_price'])
            player.updateVolume(data['quantity'])
        payloads = {}
        # Use live send back to update seller's frontend
        for player_ref in self.get_players():
            payloads[player_ref.participant.code] = {"type": 'none'}

        payloads[player.participant.code] = {
            "type": 'bets update', "cash": player.cash, "inventory": player.inventory, "bet": data}
        live._live_send_back(self.get_players()[0].participant._session_code, self.get_players()[
                             0].participant._index_in_pages, payloads)

    def input_order_file(self):
        print("setting up order")
        order_file = self.order_file()
        with open('flow_market/orders/' + order_file) as f:
            rows = list(csv.DictReader(f))
        payloads = {}
        last_timestamp = 0
        for row in rows:
            time.sleep((int(row['timestamp']) - last_timestamp)/1000)
            last_timestamp = int(row['timestamp'])
            self.get_player_by_id(int(row['trader_id'])).new_order({
                'p_min': int(row['p_min']),
                'p_max': int(row['p_max']),
                'q_max': int(row['q_max']),
                'u_max': int(row['u_max']),
                'direction': str(row['direction']),
                'status': 'active',
                'timestamp': int(row['timestamp'])
            })

            for player in self.get_players():
                payloads[player.participant.code] = {'type': str(
                    row['direction']), 'buys': self.buys(), 'sells': self.sells()}

            live._live_send_back(self.get_players()[0].participant._session_code, self.get_players()[
                                 0].participant._index_in_pages, payloads)

    def new_order(self, order, playerID, currentID):
        # print(self.order_copies)
        cache = self.order_copies
        cache[str(playerID)][str(currentID)] = {
            'player': playerID,
            'p_min': order['p_min'],
            'p_max': order['p_max'],
            'q_max': order['q_max'],
            'u_max': order['u_max'],
            'direction': order['direction'],
            'status': order['status'],
            'orderID': currentID
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
            # it seems returning 0 for demand disables execution for that specific buy order, I will use this fact in part of my implementation for preventing self trades
            return 0.0
        else:
            # The price fell p_min < price < p_max
            if((buy['p_max'] - buy['p_min']) == 0):
                return buy['q_max']
            trade_vol = buy['u_max'] * \
                ((buy['p_max'] - price) / (buy['p_max'] - buy['p_min']))
            if (trade_vol > buy['q_max']):
                # Saturate to q_max if trade_vol will exceed q_max
                return buy['q_max']
            return trade_vol

    def calcSupply(self, sell, price):
        if (price < sell['p_min']):
            # Don't trade if price is lower than min willingness to sell
            # it seems returning 0 for supply disables execution for that specific sell order, I will use this fact in part of my implementation for preventing self trades
            return 0.0
        elif (price >= sell['p_max']):
            if (sell['q_max'] < sell['u_max']):
                # Don't trade more than q_max
                return sell['q_max']
            # Trade at max rate if p >= p_max
            return sell['u_max']
        else:
            # The price fell p_min < price < p_max
            if((sell['p_max'] - sell['p_min']) == 0):
                return sell['q_max']
            trade_vol = sell['u_max'] + ((price - sell['p_max']) /
                                         (sell['p_max'] - sell['p_min'])) * sell['u_max']
            if (trade_vol > sell['q_max']):
                # Saturate to q_max if trade_vol will exceed q_max
                return sell['q_max']
            return trade_vol

    def clearingPrice(self, buys, sells):
        # Get lowest and highest prices in books
        left = 0.0
        # right = 200.0
        right = self.max_price()
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
            elif (dem < sup):  # sup > dem
                # We are right of the crossing point
                right = index
            else:
                # print("Found cross: " + str(index))
                return index

            if (curr_iter == MAX_ITERS):
                # print("Trouble finding cross in max iterations, got: " + str(index))
                return index

    # TODO should probably write docstring for this class at some point, since it's so large

    def update(self):
        buys = self.buys()
        sells = self.sells()
        payloads = {}
        if len(buys) > 0 and len(sells) > 0:
            # print("len(buys) and len(sells) > 0, executing orders")
            # Calculate the clearing price
            clearing_price = self.clearingPrice(buys, sells)
            # print("clearing price:", clearing_price)
            # print("Clearing Price: " + str(clearing_price))
            # Graph the clearing price

            for player in self.get_players():
                payloads[player.participant.code] = {
                    "type": 'clearing_price', "clearing_price": clearing_price, "buys": buys, "sells": sells}

            # READ what does this do? What is it for?
            # maybe send back clearing price for market graph?
            live._live_send_back(
                self.get_players()[0].participant._session_code,
                self.get_players()[0].participant._index_in_pages,
                payloads
            )

            # Update the traders' profits and orders
            # seems to execute sell orders regardless of what the buy order is, by which I mean there just needs to exist >1 buy order
            # TODO but what about when orders don't cross in cda? why do those orders correctly not go thru?
            # huh, this code still runs, it just doesn't do anything
            # DONE find where conditional for cda is implemented in this loop
            # trader_vol = self.calcSupply(sell, clearing_price)
            # trader_vol = self.calcDemand(buy, clearing_price)
            # when cda doesn't cross, the loops still run, but the reason no changes is because trader_vol = 0
            # so logic to prevent self orders from executing should be implemented in calcDemand()
            # print("----Sells in Update--------------------")
            for sell in sells:
                seller = self.get_player_by_id(sell['player'])

                # print("----------------------- sell ------------------------")
                # print(f'processing sell: {sell}')
                # print(f'seller: {seller}')
                # print("")
                # print(
                #     f'self.order_copies[seller.id_in_group][sell["orderID"] = [{seller.id_in_group}] [{sell["orderID"]}]')
                # print(
                #     f'self.order_copies[sell["player"]][sell["orderID"] = [{sell["player"]}] [{sell["orderID"]}]')
                # print(self.order_copies[str(
                #     seller.id_in_group)][str(sell['orderID'])])
                # print("-----------------------------------------------")

                # decrement remaining quantity of order
                trader_vol = self.calcSupply(sell, clearing_price)

                # HERE implement trading logic here

                sell['q_max'] -= trader_vol

                # print("")
                # print("------- debug begin sell ---------")

                # READ what does this do?
                cache = self.order_copies
                cache[str(seller.id_in_group)][str(
                    sell['orderID'])]['q_max'] -= trader_vol
                self.order_copies = cache
                self.save()

                # remove the order if q_max <= 0
                if sell['q_max'] <= 0.0:
                    cache = self.order_copies
                    cache[str(seller.id_in_group)][str(
                        sell['orderID'])]['status'] = 'expired'
                    self.order_copies = cache
                    self.save()
                    sell['status'] = 'expired'
                    # ReGraph KLF market since order expired
                    for player in self.get_players():
                        payloads[player.participant.code] = {
                            "type": 'regraph', "buys": buys, "sells": sells}

                    live._live_send_back(self.get_players()[0].participant._session_code, self.get_players()[
                                         0].participant._index_in_pages, payloads)

                # print(
                    # f'trader_vol: {trader_vol}, clearing_price: {clearing_price}')

                seller.updateProfit(trader_vol * clearing_price)
                seller.updateVolume(-trader_vol)

                # print("Trader " + str(sell['player']
                #                       ) + " Cash: " + str(seller.cash))
                # print("Trader " + str(sell['player']) +
                #       " Inventory: " + str(seller.inventory))

                # Use live send back to update seller's frontend
                for player in self.get_players():
                    payloads[player.participant.code] = {
                        "type": 'update', "cash": player.cash, "inventory": player.inventory}

                # payloads[seller.participant.code] = {
                #     "type": 'update', "cash": seller.cash, "inventory": seller.inventory}

                live._live_send_back(self.get_players()[0].participant._session_code, self.get_players()[
                                     0].participant._index_in_pages, payloads)

            # print("----Buys in Update--------------------")
            for buy in buys:
                buyer = self.get_player_by_id(buy['player'])

                # print("--------------------buy----------------------")
                # print(f'processing buy: {buy}')
                # print(f'buyer: {buyer}')
                # print("")
                # print(
                #     f'self.order_copies[buy["player"]][buy["orderID"] = [{buy["player"]}] [{buy["orderID"]}]')
                # print(self.order_copies[str(buy['player'])]
                #       [str(buy['orderID'])])
                # print("------------------------------------------")

                # print("")
                # print("------- debug begin buy ---------")

                # decrement remaining quantity of order
                trader_vol = self.calcDemand(buy, clearing_price)

                # HERE implement trading logic here

                buy['q_max'] -= trader_vol

                # READ what does this do?
                cache = self.order_copies
                cache[str(buy['player'])][str(buy['orderID'])
                                          ]['q_max'] -= trader_vol
                self.order_copies = cache
                self.save()

                # remove the order if q_max <= 0
                if (buy['q_max'] <= 0.0):
                    cache = self.order_copies
                    cache[str(buy['player'])][str(
                        buy['orderID'])]['status'] = 'expired'
                    self.order_copies = cache
                    self.save()
                    buy['status'] = 'expired'
                    # ReGraph KLF market since order expired
                    for player in self.get_players():
                        payloads[player.participant.code] = {
                            "type": 'regraph', "buys": buys, "sells": sells}

                    live._live_send_back(self.get_players()[0].participant._session_code, self.get_players()[
                                         0].participant._index_in_pages, payloads)

                buyer.updateProfit(-trader_vol * clearing_price)
                buyer.updateVolume(trader_vol)

                # print(
                # f'trader_vol: {trader_vol}, clearing_price: {clearing_price}')
                # print("Trader " + str(buy['player']) + " Cash: " + str(buyer.cash))
                # print("Trader " + str(buy['player']) +" Inventory: " + str(buyer.inventory))
                # Use live send back to update buyer's frontend
                for player in self.get_players():
                    payloads[player.participant.code] = {
                        "type": 'update', "cash": player.cash, "inventory": player.inventory}
                    # payloads[player.participant.code] = {"type": 'none'}

                # payloads[buyer.participant.code] = {
                #     "type": 'update', "cash": buyer.cash, "inventory": buyer.inventory}

                live._live_send_back(self.get_players()[0].participant._session_code, self.get_players()[
                                     0].participant._index_in_pages, payloads)

            # print("------- debug end ---------")
            # print("")
        else:
            # Clear the clearing price graph
            # for player in self.get_players():
            #     payloads[player.participant.code] = {"type": 'clear'}

            # live._live_send_back(self.get_players()[0].participant._session_code, self.get_players()[
            #                      0].participant._index_in_pages, payloads)

            for player in self.get_players():
                payloads[player.participant.code] = {
                    "type": 'clear', "cash": player.cash, "inventory": player.inventory}

            # payloads[seller.participant.code] = {
            #     "type": 'update', "cash": seller.cash, "inventory": seller.inventory}

            live._live_send_back(self.get_players()[0].participant._session_code, self.get_players()[
                0].participant._index_in_pages, payloads)


class Player(BasePlayer):
    cash = models.FloatField(initial=5000)
    inventory = models.FloatField(initial=500)
    num_buys = models.IntegerField(initial=0)
    num_sells = models.IntegerField(initial=0)
    # Current order states
    direction = models.StringField()  # 'buy', 'sell'
    q_max = models.IntegerField()
    u_max = models.FloatField()
    p_min = models.FloatField()
    p_max = models.FloatField()
    status = models.StringField()
    updateRunning = models.BooleanField(initial=False)

    currentID = models.StringField()

    def init_cash_inv(self):
        self.cash = self.group.start_cash()
        self.inventory = self.group.start_inv()

    def setUpdateRunning(self):
        self.updateRunning = True

    def live_method(self, data):
        # First Live message from user is to begin intialization
        if data['direction'] == 'begin':
            if not self.updateRunning:
                for p in self.group.get_players():
                    p.setUpdateRunning()
                # Setup Bets and File input
                self.group.init_order_copies()
                # ENABLE reenable set_bets
                call_with_delay(0, self.group.set_bets)
                call_with_delay(0, self.group.input_order_file)

                # Begin Continuously Updating function
                call_with_delay_infinite(
                    self.group.update_freq(), self.group.update)
            return {0: {'type': 'begin'}}

        data['trader_id'] = self.id_in_group
        if data['direction'] == 'buy_algo':
            # print(data)
            call_with_delay(0, self.group.new_buy_algo, data)
            return {0: {'type': 'buy_algo'}}

        if data['direction'] == 'sell_algo':
            call_with_delay(0, self.group.new_sell_algo, data)
            return {0: {'type': 'sell_algo'}}

        # print("got uuid:", data["orderID"])

        # BUG should be updating uuid here
        self.updateUUID(data["orderID"])

        # Input new order
        self.new_order(data)

        return_data = {'type': data['direction'], 'buys': self.group.buys(
        ), 'sells': self.group.sells()}

        return {0: return_data}

    def updateUUID(self, uuid):
        self.currentID = uuid

    # TODO make orderID unique for both all orders, not just within buys and within sells
    # not possible since each player makes their own orders and inserts their own id
    # it would be possible if Group were to make the orders
    # so for now just use player and orderID both to identify the orders
    # just going to use UUID in player
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
                             group=self.group,
                             orderID=self.currentID,
                             direction=order['direction'],
                             q_max=order['q_max'],
                             u_max=order['u_max'],
                             p_min=order['p_min'],
                             p_max=order['p_max'],
                             status=order['status'])

        self.group.new_order(order, self.id_in_group, self.currentID)

    def updateProfit(self, profit):
        self.cash += profit

    def updateVolume(self, volume):
        self.inventory += volume


class Order(ExtraModel):
    player = models.Link(Player)
    group = models.Link(Group)
    # orderID = models.IntegerField()
    orderID = models.StringField()
    direction = models.StringField()  # 'buy', 'sell'
    q_max = models.FloatField()
    u_max = models.FloatField()
    p_min = models.FloatField()
    p_max = models.FloatField()
    status = models.StringField()
