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
import copy
from timeit import default_timer as timer
import statistics
import threading
import math
import otree.common

author = 'LeepsLab'

doc = """
This is a continuous flow market game
"""

time_last = 0
times = []

# Update frontend?


class Constants(BaseConstants):
    name_in_url = 'flow_market'
    players_per_group = None
    num_rounds = 2

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
    # def creating_session(self):
    #     # ENABLE
    #     # self.group_randomly()
    #     for p in self.get_players():
    #         p.init_cash_inv()

    def creating_session(self):
        config = self.config
        if not config:
            return

        # num_silos = self.session.config['num_silos']
        num_silos = 1

        # fixed_id_in_group = not config['shuffle_role']
        fixed_id_in_group = False  # false

        # print("num_silos: ", num_silos)

        players = self.get_players()
        num_players = len(players)
        # print("num_players: ", num_players)
        silos = [[] for _ in range(num_silos)]
        for i, player in enumerate(players):
            if self.round_number == 1:
                player.silo_num = math.floor(num_silos * i/num_players)
            else:
                player.silo_num = player.in_round(1).silo_num
            silos[player.silo_num].append(player)
        # print(silos)
        group_matrix = []
        for silo in silos:
            # if config['mean_matching']:
            #     silo_matrix = [silo]
            # else:
            silo_matrix = []
            ppg = self.config['num_players']
            for i in range(0, len(silo), ppg):
                silo_matrix.append(silo[i:i+ppg])
            group_matrix.extend(otree.common._group_randomly(
                silo_matrix, fixed_id_in_group))
        # print(silo_matrix)
        # print(group_matrix)
        self.set_group_matrix(group_matrix)

        for g in self.get_groups():
            g.set_begin_time()

        for p in self.get_players():
            p.init_cash_inv()

    @property
    def config(self):
        try:
            return parse_config(self.session.config['config_file'])[self.round_number-1]
        except IndexError:
            return None


def init_copies():
    return {'1': {}, '2': {}, '3': {}, '4': {}}


class Group(BaseGroup):
    begin_time = models.FloatField()

    # probably don't need this since it can be inferred from index
    order_num = models.IntegerField(initial=0)
    round_number_old = models.IntegerField(initial=1)

    rounding_factor = models.FloatField(initial=0.00001)
    treatment_val = models.StringField()
    should_pause_after_bet = models.BooleanField(initial=False)
    # order_copies[player_id_in_group][order_id]
    order_copies = JSONField(null=True, default=init_copies)
    cancellationQueue = JSONField(null=True, default={})

    def set_begin_time(self):
        self.begin_time = time.time()

    def set_should_pause_after_bet(self, should_pause=False):
        if should_pause:
            self.should_pause_after_bet = True
            self.save()
            return self.should_pause_after_bet
        else:
            self.should_pause_after_bet = False
            self.save()
            return self.should_pause_after_bet

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
        treatment = parse_config(self.session.config['config_file'])[
            self.round_number-1]['treatment']
        self.round_number_old = self.round_number
        self.treatment_val = treatment
        self.save()
        return treatment

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

    def set_bets(self):
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
            player.record_state('begin bet')
            player.activate_bet(
                data['quantity'], data['limit_price'], data['deadline'])
            call_with_delay((int(row['deadline'])/1000),
                            self.execute_bet, data)
            rowNum += 1
        return

    def execute_bet(self, data):
        player = self.get_player_by_id(data['trader_id'])

        if data['direction'] == 'buy':
            player.updateProfit(
                data['quantity']*data['limit_price'], True, data['trader_id'] == 1)
            player.updateVolume(-data['quantity'], True)

            player.update_money_gained_from_buy_bets(
                data['quantity']*data['limit_price'])
        else:
            player.updateProfit(-data['quantity'] *
                                data['limit_price'], True, data['trader_id'] == 1)
            player.updateVolume(data['quantity'], True)

            player.update_money_lost_from_sell_bets(
                -data['quantity']*data['limit_price'])

        # Use live send back to update seller's frontend
        payloads = {}
        for player_ref in self.get_players():
            payloads[player_ref.participant.code] = {"type": 'none'}

        payloads[player.participant.code] = {
            "type": 'bets update', "cash": player.cash, "inventory": player.inventory, "bet": data, 'round': self.round_number}
        live._live_send_back(self.get_players()[0].participant._session_code, self.get_players()[
                             0].participant._index_in_pages, payloads)

        player.deactivate_bet()
        player.record_state('end bet')

    def input_order_file(self):
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
                    row['direction']), 'buys': self.buys(), 'sells': self.sells(), 'round': self.round_number, "this is it": "test"}
                print("**sending ", row['direction'],
                      "round:", self.round_number)

            live._live_send_back(self.get_players()[0].participant._session_code, self.get_players()[
                                 0].participant._index_in_pages, payloads)

    def new_algo_order(self, order, playerID, currentID):
        # TODO check if this is called from Player
        print("group algo order called")
        cache = self.order_copies
        cache[str(playerID)][str(currentID)] = {
            'player': playerID,
            'p_min': order['p_min'],
            'p_max': order['p_max'],
            'q_max': order['q_max'],
            'u_max': order['u_max'],
            'direction': order['direction'],
            'status': order['status'],
            'orderID': currentID,
            'orderNum': self.order_num,

            'executed_units': order['executed_units'],
            'q_total': order['q_total'],
            'expiration_time': order['expiration_time']
        }

        # print("***cache", cache)

        self.order_num += 1
        self.order_copies = cache
        self.save()

        print("Algo: will call addToCancellationQueue")
        call_with_delay(order['expiration_time'], self.addToCancellationQueue,
                        cache[str(playerID)][str(currentID)])

    def new_order(self, order, playerID, currentID):
        cache = self.order_copies
        cache[str(playerID)][str(currentID)] = {
            'player': playerID,
            'p_min': order['p_min'],
            'p_max': order['p_max'],
            'q_max': order['q_max'],
            'u_max': order['u_max'],
            'direction': order['direction'],
            'status': order['status'],
            'orderID': currentID,
            'orderNum': self.order_num,

            'expiration_time': order['expiration_time']
        }

        self.order_num += 1
        self.order_copies = cache
        self.save()

        call_with_delay(order['expiration_time'], self.addToCancellationQueue,
                        cache[str(playerID)][str(currentID)])

    def buys(self):
        buys_list = []
        for p in self.get_players():
            for value in self.order_copies[str(p.id_in_group)].values():
                if (self.treatment_val == "cda"):
                    condition = (value['direction'] == 'buy' and not "expired_by_cda_sell" in value) or (
                        value['direction'] == 'algo_buy' and not "expired_by_cda_sell" in value)
                    if condition:
                        buys_list.append(value)
                else:
                    condition = value['direction'] == 'buy' and value['status'] == 'active'
                    if condition:
                        buys_list.append(value)

        # Sort by time priority: earlier placed first
        return buys_list

    def sells(self):
        sells_list = []
        for p in self.get_players():
            for value in self.order_copies[str(p.id_in_group)].values():
                if (self.treatment_val == "cda"):
                    # condition = (value['direction'] == 'sell' and not "expired_by_cda_buy" in value) or (value['direction'] == 'algo_sell' and not "expired_by_cda_buy" in value)
                    condition = (
                        value['direction'] == 'sell' and not "expired_by_cda_buy" in value)

                    if value['direction'] == 'algo_sell':
                        if value['executed_units'] < value['q_total']:
                            sells_list.append(value)
                    elif condition:
                        sells_list.append(value)
                else:
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
        # print("sell:", type(sell), "price", type(price))
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
        # right = 200.0
        left = 0.0
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
        # situation #50 ends up here
        return index

    def addToCancellationQueue(self, order):
        # **cancel received order: {'p_min': 3, 'p_max': 15, 'q_max': 50, 'u_max': 3, 'direction': 'cancel_buy', 'status': 'active', 'timestamp': 21678.5, 'orderID': '482ee287-4c6b-4bc1-bc21-e449c9b82773', 'trader_id': 1}
        # self.cancellationQueue[order["orderID"]] = None
        print("Algo: addToCancellationQueue called with order:", order)
        temp = self.cancellationQueue
        temp[order["orderID"]] = None
        self.cancellationQueue = temp
        self.save()
        print("**cancel received order:", order, self.cancellationQueue)
        # problem with accessing instance variables
        # not sure how to fix, need to brainstorm
        # https://www.google.com/search?q=make+a+static+method+access+instance+variables+python&sxsrf=AOaemvJvubJgXZRGL2GpLmkruEPNENPPTw%3A1632428274334&ei=8uBMYYPmE4P5-gT86LG4BQ&oq=make+a+static+method+access+instance+variables+python&gs_lcp=Cgdnd3Mtd2l6EAMyCAghEBYQHRAeOgcIABBHELADSgQIQRgAUJwUWI0aYLkbaAFwAngBgAHvAYgB8QiSAQUxLjQuMpgBAKABAcgBCMABAQ&sclient=gws-wiz&ved=0ahUKEwiDp6ab9ZXzAhWDvJ4KHXx0DFcQ4dUDCA4&uact=5
        # print("**cancel test:", Group.buys())

    def carryOutCancellations(self):
        ordersToCancel = self.cancellationQueue.keys()
        # print("old", self.cancellationQueue)

        toDelete = []

        buys = self.buys()
        sells = self.sells()

        for orderID in ordersToCancel:
            # print("orderID", orderID)

            cache = self.order_copies
            print("old cache", cache)
            # Search for order
            for p in self.get_players():
                for orderKey in self.order_copies[str(p.id_in_group)]:
                    if orderKey == orderID:
                        toDelete.append(orderID)
                        # print("found", orderKey,
                        #       self.order_copies[str(p.id_in_group)][orderKey])
                        cache[str(p.id_in_group)
                              ][orderID]["status"] = "expired"

                        if (self.treatment_val == "cda"):
                            # cache[str(p.id_in_group)][orderID]["direction"] = "expired_by_cda_sell"
                            if (cache[str(p.id_in_group)][orderID]["direction"] == "sell" or cache[str(p.id_in_group)][orderID]["direction"] == "algo_sell"):
                                cache[str(p.id_in_group)
                                      ][orderID]["expired_by_cda_buy"] = True
                            if (cache[str(p.id_in_group)][orderID]["direction"] == "buy" or cache[str(p.id_in_group)][orderID]["direction"] == "algo_buy"):
                                cache[str(p.id_in_group)
                                      ][orderID]["expired_by_cda_sell"] = True

                        payloads = {}
                        for player in self.get_players():
                            payloads[player.participant.code] = {
                                "type": 'regraph', "buys": buys, "sells": sells, 'round': self.round_number}

                        live._live_send_back(self.get_players()[0].participant._session_code, self.get_players()[
                            0].participant._index_in_pages, payloads)
                p.record_state("cancelled order")

            self.order_copies = cache
            self.save()
            print("new cache", cache)

        cache = self.cancellationQueue
        for id in toDelete:
            del cache[id]

        self.cancellationQueue = cache
        self.save()
        # print("new", self.cancellationQueue)

        # for p in self.get_players():
        #     for value in self.order_copies[str(p.id_in_group)].values():
        #         if (self.treatment_val == "cda"):
        #             if value['direction'] == 'buy' and not "expired_by_cda_sell" in value:
        #                 buys_list.append(value)
        #         else:
        #             if value['direction'] == 'buy' and value['status'] == 'active':
        #                 buys_list.append(value)
        # return buys_list

        # **cont
        # cache[str(seller.id_in_group)][str(
        #     sell['orderID'])]['status'] = 'expired'
        # self.order_copies = cache
        # self.save()
        # sell['status'] = 'expired'
        # # ReGraph KLF market since order expired
        # # should_update_market_graph = True  # BUG think this is causing a bug
        # for player in self.get_players():
        #     payloads[player.participant.code] = {
        #         "type": 'regraph', "buys": buys, "sells": sells, 'round': self.round_number}

        # live._live_send_back(self.get_players()[0].participant._session_code, self.get_players()[
        #                         0].participant._index_in_pages, payloads)

    # def update(self):
    #     global time_last
    #     current_time = time.perf_counter()
    #     global times
    #     if len(times) > 50:
    #         # pass
    #         del times[0:48]
    #     times.append(current_time-time_last)
    #     print("avg time elapsed:", statistics.median(times))
    #     time_last = current_time

    def update(self):
        # TEST does this update function follow frequency in config?
        # global time_last
        # current_time = time.perf_counter()
        # global times
        # if len(times) > 50:
        #     # pass
        #     del times[0:48]
        # times.append(current_time-time_last)
        # print("avg time elapsed:", statistics.median(times))
        # time_last = current_time

        self.carryOutCancellations()

        buys = self.buys()
        sells = self.sells()
        payloads = {}
        should_update_market_graph = False

        condition = None
        print("\n\n")
        print("buys:", buys)
        print("sells:", sells)

        # change condition to true if there is an algo order in list
        if (self.treatment_val == "cda"):
            condition = len(buys) > 0 or len(sells) > 0
        if (self.treatment_val == "flo"):
            condition = len(buys) > 0 and len(sells) > 0

        if condition:
            # Calculate the clearing price
            clearing_price = self.clearingPrice(buys, sells)

            # Graph the clearing price
            for player in self.get_players():
                payloads[player.participant.code] = {
                    "type": 'clearing_price', "clearing_price": clearing_price, "buys": buys, "sells": sells, 'round': self.round_number}

            live._live_send_back(
                self.get_players()[0].participant._session_code,
                self.get_players()[0].participant._index_in_pages,
                payloads
            )

            # Update the traders' profits and orders
            # Determine values required for CDA: best_bid, best_ask and max_price, min_price
            best_bid = None
            max_price = float('-inf')
            for obj in buys:
                # if (obj["p_max"] > max_price and obj['status'] != 'expired'):
                if (obj["p_max"] > max_price and not ("expired_by_cda_sell" in obj)):
                    max_price = obj["p_max"]
                    best_bid = obj

            best_ask = None
            min_price = float('inf')
            for obj in sells:
                if (obj["p_max"] < min_price and not ("expired_by_cda_buy" in obj['status'])):
                    min_price = obj["p_max"]
                    best_ask = obj

            # Determine CDA clearing price
            cda_clearing_price = None
            if (best_ask != None and best_bid != None):
                if (best_ask["orderNum"] < best_bid["orderNum"]):
                    cda_clearing_price = best_ask["p_max"]
                else:
                    cda_clearing_price = best_bid["p_max"]
            else:
                print("ERROR best_ask", best_ask, "best_bid", best_bid)

            future_tx_volume = None

            for sell in sells:
                # Required for CDA execution: add an additional key to the best_bid item
                if (best_bid != None and not ("q_max_cda_copy" in best_bid)):
                    best_bid["q_max_cda_copy"] = best_bid["q_max"]
                if (not ("q_max_cda_copy" in sell)):
                    sell["q_max_cda_copy"] = sell["q_max"]

                seller = self.get_player_by_id(sell['player'])
                best_bid_q = None
                tx_volume = None

                if (self.treatment_val == "cda" and best_bid != None and sell['p_max'] <= best_bid['p_max']):
                    if sell['q_max_cda_copy'] > best_bid["q_max_cda_copy"]:  # TODO look into
                        print("****sell tx_volume 0")
                        print("****sell", sell)
                        print("****best_bid", best_bid)

                        tx_volume = best_bid["q_max_cda_copy"]

                        sell_q = sell['q_max_cda_copy']
                        best_bid_q = best_bid['q_max_cda_copy']

                        sell['q_max_cda_copy'] -= best_bid_q
                        best_bid['q_max_cda_copy'] = 0
                        best_bid['expired_by_cda_sell'] = True

                        future_tx_volume = best_bid_q
                    elif sell['q_max_cda_copy'] == best_bid["q_max_cda_copy"]:
                        print("****sell tx_volume 1")
                        print("****sell", sell)
                        print("****best_bid", best_bid)

                        tx_volume = sell['q_max_cda_copy']

                        sell_q = sell['q_max_cda_copy']
                        best_bid_q = best_bid['q_max_cda_copy']

                        sell['q_max_cda_copy'] -= best_bid_q
                        best_bid['q_max_cda_copy'] -= sell_q
                        best_bid['expired_by_cda_sell'] = True

                        future_tx_volume = sell_q
                    else:  # TODO look into
                        print("****sell tx_volume 2")
                        print("****sell", sell)
                        print("****best_bid", best_bid)

                        tx_volume = sell['q_max_cda_copy']

                        sell_q = sell['q_max_cda_copy']
                        best_bid_q = best_bid['q_max_cda_copy']

                        sell['q_max_cda_copy'] = 0
                        best_bid['q_max_cda_copy'] -= sell_q

                        future_tx_volume = sell_q

                        pass
                    seller.update_trading_state(
                        True, '-', best_bid['p_max'], sell_q)

                elif self.treatment_val == "flo":  # TODO copy
                    # Decrement remaining quantity of order
                    trader_vol = self.calcSupply(sell, clearing_price)
                    sell['q_max'] -= trader_vol
                    seller.update_trading_state(
                        True, '-', clearing_price, trader_vol)

                cache = self.order_copies

                self.order_copies = cache
                self.save()

                # Update seller's profit and volume. TBH I need to look into what this actually does... I think it's for updating values in the database
                if (self.treatment_val == "cda" and best_bid != None and sell['p_max'] <= best_bid['p_max']):
                    print("***sell:", sell)
                    print("***best_bid:", best_bid)
                    # print("**sell update player.cash:", player.cash, "best_bid_q:",
                    #       best_bid['q_max'], "clearing_price:", cda_clearing_price, "best_bid_q*clearing_price:", best_bid["q_max"] * cda_clearing_price)
                    # seller.updateProfit(
                    #     best_bid["q_max"] * cda_clearing_price, False, sell['player'] == 1)
                    # seller.updateVolume(-best_bid["q_max"])
                    seller.updateProfit(
                        tx_volume * cda_clearing_price, False, sell['player'] == 1)
                    seller.updateVolume(-tx_volume)

                    if "executedProfit" not in sell:
                        sell['executedProfit'] = 0
                    if "executedVolume" not in sell:
                        sell['executedVolume'] = 0

                    # sell['executedProfit'] += best_bid["q_max"] * \
                    #     cda_clearing_price
                    # sell['executedVolume'] += -best_bid["q_max"]
                    sell['executedProfit'] += tx_volume * \
                        cda_clearing_price
                    sell['executedVolume'] += -tx_volume
                elif self.treatment_val == 'flo':
                    seller.updateProfit(trader_vol * clearing_price)
                    seller.updateVolume(-trader_vol)

                    if "executedProfit" not in sell:
                        sell['executedProfit'] = 0
                    if "executedVolume" not in sell:
                        sell['executedVolume'] = 0

                    sell['executedProfit'] += trader_vol * clearing_price
                    sell['executedVolume'] += -trader_vol

                self.save()

                # Expire the order depending on various conditions...
                # Like removing the order if q_max <= 0
                if (self.treatment_val == "flo" and sell['q_max'] <= self.rounding_factor) or (self.treatment_val == "cda" and sell["q_max_cda_copy"] <= self.rounding_factor):
                    cache = self.order_copies
                    cache[str(sell['player'])][str(
                        sell['orderID'])]['status'] = 'expired'
                    self.order_copies = cache
                    self.save()
                    sell['status'] = 'expired'
                    seller.update_trading_state(False, None, None, None)

                    if sell['direction'] == 'algo_sell':
                        sell['executed_units'] += sell['q_max']

                        if sell['executed_units'] < sell['q_total']:
                            #   if q_total - executed_units >= q_max (units at a time)
                            #       reset
                            if sell['q_total'] - sell['executed_units'] >= sell['q_max']:
                                # reset
                                # 'status': 'expired' 'q_max_cda_copy': 0, 'expired_by_cda_sell': True
                                print("Algo debug algo_sell 1:", sell)
                                sell['status'] = 'active'

                                if ('q_max_cda_copy' in sell):
                                    del sell['q_max_cda_copy']
                                if ('expired_by_cda_buy' in sell):
                                    del sell['expired_by_cda_buy']

                                cache = self.order_copies
                                cache[str(sell['player'])][str(
                                    sell['orderID'])]['status'] = 'active'
                                self.order_copies = cache
                                self.save()

                                print("*TODO algo1: ", sell)
                            else:
                                #   else (should set units at a time to a smaller value)
                                #       reset but set units at a time = q_total - executed_units
                                print("Algo debug algo_sell 2:", sell)

                                sell['q_max'] = sell['q_total'] - \
                                    sell['executed_units']

                                sell['status'] = 'active'
                                del sell['q_max_cda_copy']
                                del sell['expired_by_cda_buy']

                                cache = self.order_copies
                                cache[str(sell['player'])][str(
                                    sell['orderID'])]['status'] = 'active'
                                self.order_copies = cache
                                self.save()

                                print("*TODO algo2: ", sell)

                    ###########################################################

                    # ReGraph KLF market since order expired
                    # should_update_market_graph = True  # BUG think this is causing a bug
                    for player in self.get_players():
                        payloads[player.participant.code] = {
                            "type": 'regraph', "buys": buys, "sells": sells, 'round': self.round_number}
                        player.record_state("expired order")

                    live._live_send_back(self.get_players()[0].participant._session_code, self.get_players()[
                                         0].participant._index_in_pages, payloads)

                    print("**sell order expired: ", sell)

                # Use live send back to update seller's frontend
                for player in self.get_players():
                    payloads[player.participant.code] = {
                        "type": 'update', "cash": player.cash, "inventory": player.inventory, "payoff_data": player.get_payoff_data(), 'round': self.round_number}

                print("*graph update")

                live._live_send_back(self.get_players()[0].participant._session_code, self.get_players()[
                                     0].participant._index_in_pages, payloads)

            # This should be a mirror image of the "for sell in sells" loop
            for buy in buys:
                buyer = self.get_player_by_id(buy['player'])

                best_ask = None
                min_price = float('inf')
                for obj in sells:
                    if (obj["p_max"] < min_price and not ("expired_by_cda_buy" in obj)):
                        min_price = obj["p_max"]
                        best_ask = obj

                if (best_ask != None and not ("q_max_cda_copy" in best_ask)):
                    best_ask["q_max_cda_copy"] = best_ask["q_max"]

                if (not ("q_max_cda_copy" in buy)):
                    buy["q_max_cda_copy"] = buy["q_max"]

                tx_volume = None

                if (self.treatment_val == "cda" and best_ask != None and buy['p_max'] >= best_ask['p_max']):
                    if buy['q_max_cda_copy'] > best_ask["q_max_cda_copy"]:
                        print("****tx_volume 0")
                        print("****buy", buy)
                        print("****best_ask", best_ask)
                        tx_volume = best_ask["q_max_cda_copy"]
                        if (tx_volume == 0):
                            tx_volume = future_tx_volume
                        print("****tx_volume", tx_volume)

                        buy_q = buy['q_max_cda_copy']
                        best_ask_q = best_ask['q_max_cda_copy']

                        buy['q_max_cda_copy'] -= best_ask_q
                        best_ask['q_max_cda_copy'] = 0
                        best_ask['expired_by_cda_buy'] = True

                    elif buy['q_max_cda_copy'] == best_ask["q_max_cda_copy"]:
                        print("****tx_volume 1")
                        print("****buy", buy)
                        print("****best_ask", best_ask)
                        tx_volume = buy['q_max_cda_copy']
                        if (tx_volume == 0):
                            tx_volume = future_tx_volume
                        print("****tx_volume", tx_volume)

                        buy_q = buy['q_max_cda_copy']
                        best_ask_q = best_ask['q_max_cda_copy']

                        buy['q_max_cda_copy'] -= best_ask_q
                        best_ask['q_max_cda_copy'] -= buy_q
                        best_ask['expired_by_cda_buy'] = True

                        pass
                    else:
                        print("****tx_volume 2")
                        print("****buy", buy)
                        print("****best_ask", best_ask)
                        tx_volume = buy['q_max_cda_copy']
                        if (tx_volume == 0):
                            tx_volume = future_tx_volume
                        print("****tx_volume", tx_volume)

                        buy_q = buy['q_max_cda_copy']
                        best_ask_q = best_ask['q_max_cda_copy']

                        buy['q_max_cda_copy'] = 0
                        best_ask['q_max_cda_copy'] -= buy_q
                        pass
                    buyer.update_trading_state(
                        True, '+', best_ask['p_max'], buy_q)
                elif (self.treatment_val == "flo"):
                    # decrement remaining quantity of order
                    trader_vol = self.calcDemand(buy, clearing_price)
                    buy['q_max'] -= trader_vol
                    buyer.update_trading_state(
                        True, '+', clearing_price, trader_vol)
                else:
                    if (best_ask != None):
                        pass
                cache = self.order_copies

                self.order_copies = cache
                self.save()

                # update player cash and inventory
                if (self.treatment_val == "cda" and best_ask != None and buy['p_max'] >= best_ask['p_max']):
                    # if best_bid is algo_buy or sell is algo_sell, use the lower q_max of the two
                    # if algo buy, then use algo_price
                    print("***buy:", buy)
                    print("***best_ask:", best_ask)
                    # print("**buy update price old:", player.cash, "best_ask_q:",
                    #       best_ask['q_max'], "clearing price:", cda_clearing_price, "-best_ask_q*clearing_price:", -best_ask["q_max"] * cda_clearing_price)
                    # buyer.updateProfit(-best_ask["q_max"] *
                    #                    cda_clearing_price, False, buy["player"] == 1)
                    # buyer.updateVolume(best_ask["q_max"])

                    print("***tx_volume:", tx_volume, "cda_clearing_price:",
                          cda_clearing_price, "updateProfit:", -tx_volume*cda_clearing_price)

                    buyer.updateProfit(-tx_volume *
                                       cda_clearing_price, False, buy["player"] == 1)
                    buyer.updateVolume(tx_volume)

                    if "executedProfit" not in buy:
                        buy['executedProfit'] = 0
                    if "executedVolume" not in buy:
                        buy['executedVolume'] = 0

                    buy['executedProfit'] += - \
                        tx_volume * cda_clearing_price
                    buy['executedVolume'] += tx_volume

                elif self.treatment_val == "flo":
                    buyer.updateProfit(-trader_vol * clearing_price)
                    buyer.updateVolume(trader_vol)

                    if "executedProfit" not in buy:
                        buy['executedProfit'] = 0
                    if "executedVolume" not in buy:
                        buy['executedVolume'] = 0

                    buy['executedProfit'] += -trader_vol * clearing_price
                    buy['executedVolume'] += trader_vol

                self.save()

                # Remove the order if q_max <= 0
                # If (buy['q_max'] <= 0.0):
                if (self.treatment_val == "flo" and buy['q_max'] <= self.rounding_factor) or (self.treatment_val == "cda" and buy["q_max_cda_copy"] <= self.rounding_factor):

                    cache = self.order_copies
                    cache[str(buy['player'])][str(
                        buy['orderID'])]['status'] = 'expired'
                    self.order_copies = cache
                    self.save()
                    buy['status'] = 'expired'

                    buyer.update_trading_state(False, None, None, None)

                    print("EXPIRED buy", buy)

                    # Add q_max (units at a time) to executed_units
                    # If executed_units < q_total
                    if buy['direction'] == 'algo_buy':
                        buy['executed_units'] += buy['q_max']
                        print("*TODO algo: buy algo order expired: ", buy)
                        if buy['executed_units'] < buy['q_total']:
                            #   If q_total - executed_units >= q_max (units at a time)
                            #       Reset
                            if buy['q_total'] - buy['executed_units'] >= buy['q_max']:
                                # Reset
                                # 'status': 'expired' 'q_max_cda_copy': 0, 'expired_by_cda_sell': True
                                print("Algo debug algo_buy:", buy)
                                buy['status'] = 'active'
                                del buy['q_max_cda_copy']
                                del buy['expired_by_cda_sell']

                                cache = self.order_copies
                                cache[str(buy['player'])][str(
                                    buy['orderID'])]['status'] = 'active'
                                self.order_copies = cache
                                self.save()

                                print("*TODO algo1: ", buy)
                            else:
                                #   Else (should set units at a time to a smaller value)
                                #       Reset but set units at a time = q_total - executed_units

                                buy['q_max'] = buy['q_total'] - \
                                    buy['executed_units']

                                buy['status'] = 'active'
                                del buy['q_max_cda_copy']
                                del buy['expired_by_cda_sell']

                                cache = self.order_copies
                                cache[str(buy['player'])][str(
                                    buy['orderID'])]['status'] = 'active'
                                self.order_copies = cache
                                self.save()

                                print("*TODO algo2: ", buy)

                    ###########################################################

                    # ReGraph KLF market since order expired
                    for player in self.get_players():
                        payloads[player.participant.code] = {
                            "type": 'regraph', "buys": buys, "sells": sells, 'round': self.round_number}
                        player.record_state("expired order")

                    live._live_send_back(self.get_players()[0].participant._session_code, self.get_players()[
                                         0].participant._index_in_pages, payloads)

                elif should_update_market_graph:
                    for player in self.get_players():
                        payloads[player.participant.code] = {
                            "type": 'regraph', "buys": buys, "sells": sells, 'round': self.round_number}

                    live._live_send_back(self.get_players()[0].participant._session_code, self.get_players()[
                                         0].participant._index_in_pages, payloads)

                # Use live send back to update buyer's frontend
                for player in self.get_players():
                    payloads[player.participant.code] = {
                        "type": 'update', "cash": player.cash, "inventory": player.inventory, "payoff_data": player.get_payoff_data(), 'round': self.round_number}

                live._live_send_back(self.get_players()[0].participant._session_code, self.get_players()[
                                     0].participant._index_in_pages, payloads)
        else:
            # Clear the clearing price graph
            playerIndex = 0

            for player in self.get_players():
                playerIndex += 1
                payloads[player.participant.code] = {
                    "type": 'clear', "cash": player.getCash(), "inventory": player.inventory, "payoff_data": player.get_payoff_data(), 'round': self.round_number}

            live._live_send_back(self.get_players()[0].participant._session_code, self.get_players()[
                0].participant._index_in_pages, payloads)


class Player(BasePlayer):
    silo_num = models.IntegerField()

    cash = models.FloatField(initial=5000)
    inventory = models.FloatField(initial=500)
    num_buys = models.IntegerField(initial=0)
    num_sells = models.IntegerField(initial=0)
    num_sells = models.IntegerField(initial=0)

    # Payoff
    endowment = models.FloatField(initial=0)
    money_gained_in_market = models.FloatField(initial=0)
    money_lost_in_market = models.FloatField(initial=0)

    money_gained_from_buy_bets = models.FloatField(initial=0)
    money_lost_from_sell_bets = models.FloatField(initial=0)

    c_bar = models.FloatField(initial=100)
    negative_inventory = models.FloatField(initial=0)

    # payoff = models.FloatField(initial=0)

    # Current order states
    direction = models.StringField()  # 'buy', 'sell'
    q_max = models.IntegerField()
    u_max = models.FloatField()
    p_min = models.FloatField()
    p_max = models.FloatField()
    status = models.StringField()

    executed_units = models.IntegerField()
    q_total = models.IntegerField()
    expiration_time = models.IntegerField()

    updateRunning = models.BooleanField(initial=False)
    currentID = models.StringField()

    trading = models.BooleanField(initial=False)
    sign = models.StringField()
    trading_price = models.FloatField()
    trading_rate = models.FloatField()

    active_bet = models.BooleanField(initial=False)
    bet_quantity = models.IntegerField()
    bet_price = models.IntegerField()
    bet_deadline = models.IntegerField()

    def init_cash_inv(self):
        self.cash = self.group.start_cash()
        self.inventory = self.group.start_inv()
        self.update_endowment(self.cash)
        self.save()

    def update_payoff(self):
        a = self.endowment + self.money_gained_in_market - self.money_lost_in_market
        b = self.money_gained_from_buy_bets - self.money_lost_from_sell_bets
        c = self.c_bar * self.negative_inventory
        self.payoff = a + b - c
        self.save()

    def get_payoff_data(self):
        self.update_payoff()

        return {
            "payoff": self.payoff,
            "endowment": self.endowment,
            "money_gained_in_market": self.money_gained_in_market,
            "money_lost_in_market": self.money_lost_in_market,
            "money_gained_from_buy_bets": self.money_gained_from_buy_bets,
            "money_lost_from_sell_bets": self.money_lost_from_sell_bets,
            "c_bar": self.c_bar,
            "negative_inventory": self.negative_inventory,
        }

    # Done automatically in this class
    def update_endowment(self, val):
        self.endowment = val
        self.save()

    # Done automatically in this class
    def update_money_gained_in_market(self, val):
        self.money_gained_in_market += abs(val)
        self.save()  # just use this

    # Done automatically in this class
    def update_money_lost_in_market(self, val):
        self.money_lost_in_market += abs(val)
        self.save()

    def update_money_gained_from_buy_bets(self, val):
        self.money_gained_from_buy_bets += abs(val)
        self.save()

    def update_money_lost_from_sell_bets(self, val):
        self.money_lost_from_sell_bets += abs(val)
        self.save()

    # Done automatically in this class
    def update_negative_inventory(self):
        if self.inventory < 0:
            self.negative_inventory = abs(self.inventory)
        else:
            self.negative_inventory = 0
        self.save()

    def setUpdateRunning(self):
        self.updateRunning = True
        self.save()

    def live_method(self, data):
        # First Live message from user is to begin intialization
        if data['direction'] == 'begin':
            if not self.updateRunning:
                for p in self.group.get_players():
                    p.setUpdateRunning()
                # Setup Bets and File input
                self.group.init_order_copies()
                # # ENABLE reenable set_bets
                call_with_delay(0, self.group.set_bets)
                call_with_delay(0, self.group.input_order_file)

                # Begin Continuously Updating function
                call_with_delay_infinite(
                    self.group.update_freq(), self.group.update)
            return {0: {'type': 'begin'}}

        data['trader_id'] = self.id_in_group

        self.updateUUID(data["orderID"])

        if data['direction'] == "cancel":
            print("**cancel buy")
            self.group.addToCancellationQueue(data)
        else:
            if data['direction'] == 'algo_buy' or data['direction'] == 'algo_sell':
                self.new_algo_order(data)
            else:
                # Input new order
                print("**expirationDebug:", data)
                self.new_order(data)

            return_data = {'type': data['direction'], 'buys': self.group.buys(
            ), 'sells': self.group.sells(), 'round': self.round_number}

            return {0: return_data}

        return

    def updateUUID(self, uuid):
        self.currentID = uuid

    def new_algo_order(self, order):
        print("*error2")
        self.direction = order['direction']
        self.q_max = order['q_max']
        self.u_max = order['u_max']
        self.p_min = order['p_min']
        self.p_max = order['p_max']
        self.status = order['status']

        self.executed_units = order['executed_units']
        self.q_total = order['q_total']
        self.expiration_time = order['expiration_time']

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
                             status=order['status'],

                             executed_units=order['executed_units'],
                             q_total=order['q_total'],
                             expiration_time=order['expiration_time'])

        # self.group.new_order(order, self.id_in_group, self.currentID)
        self.group.new_algo_order(order, self.id_in_group, self.currentID)

    def new_order(self, order):
        self.direction = order['direction']
        self.q_max = order['q_max']
        self.u_max = order['u_max']
        self.p_min = order['p_min']
        self.p_max = order['p_max']
        self.status = order['status']

        self.expiration_time = order['expiration_time']

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
                             status=order['status'],
                             expiration_time=order['expiration_time'])

        for p in self.group.get_players():
            p.record_state('new order')  # Record State on New Order

        self.group.new_order(order, self.id_in_group, self.currentID)

    def record_state(self, event):
        State.objects.create(player=self,
                             group=self.group,
                             cash=self.cash,
                             inventory=self.inventory,
                             trading=self.trading,
                             sign=self.sign,
                             trading_price=self.trading_price,
                             trading_rate=self.trading_rate,
                             bet=self.active_bet,
                             bet_quantity=self.bet_quantity,
                             bet_price=self.bet_price,
                             bet_deadline=self.bet_deadline,
                             time=(time.time() - self.group.begin_time),
                             event=event)

    def update_trading_state(self, trading, sign, price, rate):
        self.trading = trading
        self.sign = sign
        self.trading_price = price
        self.trading_rate = rate

    def activate_bet(self, quantity, price, deadline):
        self.active_bet = True
        self.bet_quantity = quantity
        self.bet_price = price
        self.bet_deadline = deadline

    def deactivate_bet(self):
        self.active_bet = False
        self.bet_quantity = None
        self.bet_price = None
        self.bet_deadline = None

    def updateProfit(self, profit, calling_from_bets=False, debug=False):
        self.cash += profit
        self.save()
        # if (calling_from_bets):
        #     self.save()

        if (not calling_from_bets):
            if profit > 0:
                self.update_money_gained_in_market(profit)
            if profit < 0:
                self.update_money_lost_in_market(profit)

    def getCash(self):
        return self.cash

    def updateVolume(self, volume, calling_from_bets=False):
        self.inventory += volume
        self.save()

        self.update_negative_inventory()


class Order(ExtraModel):
    player = models.Link(Player)
    group = models.Link(Group)
    orderID = models.StringField()
    direction = models.StringField()  # 'buy', 'sell'
    q_max = models.FloatField()
    u_max = models.FloatField()
    p_min = models.FloatField()
    p_max = models.FloatField()
    status = models.StringField()

    executed_units = models.IntegerField()
    q_total = models.IntegerField()
    expiration_time = models.IntegerField()


class State(ExtraModel):
    player = models.Link(Player)
    group = models.Link(Group)

    cash = models.FloatField()
    inventory = models.FloatField()

    trading = models.BooleanField()
    sign = models.StringField()
    trading_price = models.FloatField()
    trading_rate = models.FloatField()

    bet = models.BooleanField()  # Active or Inactive
    # If Active
    bet_quantity = models.IntegerField()
    bet_price = models.IntegerField()
    bet_deadline = models.IntegerField()

    time = models.FloatField()

    event = models.StringField()


def custom_export(players):
    yield ['participant', 'cash', 'inventory', 'trading', 'trading_sign', 'trading_price', 'trading_rate', 'bet', 'bet_quantity', 'bet_price', 'bet_deadline', 'time', 'event']

    for player in players:
        participant = player.participant

        states = State.objects.filter(player=player)

        for s in states:
            yield [participant.code, s.cash, s.inventory, s.trading, s.sign, s.trading_price, s.trading_rate, s.bet, s.bet_quantity, s.bet_price, s.bet_deadline, s.time, s.event]
