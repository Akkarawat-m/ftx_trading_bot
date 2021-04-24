### JUST FOR LEARNING PURPOSE USE AT YOUR OWN RISK !!!!! ####

# import neccessary package

import ccxt
import json
import pandas as pd
import time
import decimal
from datetime import datetime

# Api and secret
api_key = ""  
api_secret = ""
subaccount = ""
account_name = ""  # Set your account name (ตั้งชื่อ Account ที่ต้องการให้แสดงผล)



# Exchange Details
exchange = ccxt.ftx({
    'apiKey': api_key,
    'secret': api_secret,
    'enableRateLimit': True}
)
exchange.headers = {'FTX-SUBACCOUNT': subaccount,}
post_only = True  # Maker or Taker (วางโพซิชั่นเป็น MAKER เท่านั้นหรือไม่ True = ใช่)

# Global Varibale Setting
min_reb_size = 5  # Minimum Rebalance Size ($)
token_name_lst =["XRP", "XRPBEAR"]  # Name of Rebalancing Token (ใส่ชื่อเหรียญที่ต้องการ Rebalance)
pair_lst = ["XRP/USD", "XRPBEAR/USD"]  # Rebalancing Pair (ใส่ชื่อคู่ที่ต้องการ Rebalance เช่น XRP จะเป็น XRP/USD)
fix_value_lst = [30, 40]  # Rebalancing Ratio (ใส่สัดส่วนที่ต้องการ Rebalance หน่วยเป็น $)

# file system
tradelog_file = "{}_tradinglog.csv".format(subaccount)
trading_call_back = 10

# Rebalance Condition
time_sequence = [3, 1, 4, 1, 5, 9, 2]  # Rebalancing Time Sequence (เวลาที่จะใช้ในการ Rebalance ใส่เป็นเวลาเดี่ยว หรือชุดตัวเลขก็ได้)

# List to Dict Setting
token_fix_value = {token_name_lst[i]: fix_value_lst[i] for i in range(len(token_name_lst))}
pair_dict = {token_name_lst[i]: pair_lst[i] for i in range(len(token_name_lst))}



### Function Part ###

def get_time():  # เวลาปัจจุบัน
    named_tuple = time.localtime() # get struct_time
    Time = time.strftime("%m/%d/%Y, %H:%M:%S", named_tuple)
    return Time

def get_price():
    price = exchange.fetch_ticker(pair)['last']
    return price

def get_ask_price():
    ask_price = exchange.fetch_ticker(pair)['ask']
    return ask_price

def get_bid_price():
    bid_price = exchange.fetch_ticker(pair)['bid']
    return bid_price

def get_pending_buy():
    pending_buy = []
    for i in exchange.fetch_open_orders(pair):
        if i['side'] == 'buy':
            pending_buy.append(i['info'])
    return pending_buy

def get_pending_sell():
    pending_sell = []
    for i in exchange.fetch_open_orders(pair):
        if i['side'] == 'sell':
            pending_sell.append(i['info'])
    return pending_sell

def create_buy_order():
    # Order Parameter
    types = 'limit'
    side = 'buy'
    size = buy_size
    price = buy_price
    exchange.create_order(pair, types, side, size, price, {'postOnly': post_only})
    print("{} Buy Order Created".format(asset_name))
    
def create_sell_order():
    # Order Parameter
    types = 'limit'
    side = 'sell'
    size = sell_size
    price = sell_price
    exchange.create_order(pair, types, side, size, price, {'postOnly': post_only})
    print("{} Sell Order Created".format(asset_name))
    
def cancel_order():
    exchange.cancel_order(order_id)
    print("Order ID : {} Successfully Canceled".format(order_id))

def get_minimum_size():
    minimum_size = float(exchange.fetch_ticker(pair)['info']['minProvideSize'])
    return minimum_size

def get_step_size():
    step_size = float(exchange.fetch_ticker(pair)['info']['sizeIncrement'])
    return step_size

def get_step_price():
    step_price = float(exchange.fetch_ticker(pair)['info']['priceIncrement'])
    return step_price

def get_min_trade_value():
    min_trade_value = float(exchange.fetch_ticker(pair)['info']['sizeIncrement']) * price
    return min_trade_value

def get_wallet_details():
    wallet = exchange.privateGetWalletBalances()['result']
    return wallet

def get_cash():
    wallet = exchange.privateGetWalletBalances()['result']
    for t in wallet:
        if t['coin'] == 'USD':
            cash = float(t['availableWithoutBorrow'] )
    return cash

# Database Function Part

def checkDB():
    try:
        tradinglog = pd.read_csv("{}_tradinglog.csv".format(subaccount))
        print('DataBase Exist Loading DataBase....')
    except:
        tradinglog = pd.DataFrame(columns=['id', 'timestamp', 'datetime', 'symbol', 'side', 'price', 'amount', 'cost', 'fee'])
        tradinglog.to_csv("{}_tradinglog.csv".format(subaccount),index=False)
        print("Database Created")
        
        
    return tradinglog

# Database Setup
print('Checking Database file.....')
tradinglog = checkDB()

def get_trade_history(pair):
    pair = pair
    trade_history = pd.DataFrame(exchange.fetchMyTrades(pair, limit = trading_call_back),
                              columns=['id', 'timestamp', 'datetime', 'symbol', 'side', 'price', 'amount', 'cost', 'fee'])
    
    cost=[]
    for i in range(len(trade_history)):
        cost.append((trade_history['fee'][i]['cost']))  # ใน fee เอาแค่ cost
    
    trade_history['fee'] = cost
    
    return trade_history

def get_last_id(pair):
    pair = pair
    trade_history = get_trade_history(pair)
    last_trade_id = (trade_history.iloc[:trading_call_back]['id'])
    
    return last_trade_id

def update_trade_log(pair):
    pair = pair
    tradinglog = pd.read_csv("{}_tradinglog.csv".format(subaccount))
    last_trade_id = get_last_id(pair)
    trade_history = get_trade_history(pair)
    
    for i in last_trade_id:
        tradinglog = pd.read_csv("{}_tradinglog.csv".format(subaccount))
        trade_history = get_trade_history(pair)
    
        if int(i) not in tradinglog.values:
            print(i not in tradinglog.values)
            last_trade = trade_history.loc[trade_history['id'] == i]
            tradinglog = pd.concat([last_trade,tradinglog],ignore_index=True)
            tradinglog.to_csv("{}_tradinglog.csv".format(subaccount),index=False)
            print('Recording Trade ID : {}'.format(i))
        else:
            print('Trade Already record')


# Status Report
while True:
    try:    
        wallet = get_wallet_details()
        cash = get_cash()
        Time = get_time()

        print('Time : {}'.format(Time))
        print('Account : {}'.format(account_name))
        print('Your Remaining Balance : {}'.format(cash))
        print('Checking Your Asset')

        total_asset = 0

        for item in wallet:
            asset_value = round(float(item['usdValue']),2)
            total_asset += asset_value
            
        print('Your Total Asset Value is : {}'.format(total_asset))
        print("------------------------------")

        # Checking Initial Balance Loop
        while len(wallet) < len(token_name_lst) + 1:

            print('Entering Initial Loop')
            print("------------------------------")
            
            wallet = get_wallet_details()
            asset_in_wallet = [item['coin'] for item in wallet]
            print("Wallet Asset < Setting")

            for asset_name in token_fix_value:
                if asset_name not in asset_in_wallet:
                    print('{} is missing'.format(asset_name))
                    print('Checking {} Buy Condition ......'.format(format(asset_name)))

                    # Get price params
                    pair = pair_dict[asset_name]
                    price = get_price()
                    ask_price = get_ask_price()
                    bid_price = get_bid_price()

                    # Trade history Checking

                    print('Validating Trading History')
                    update_trade_log(pair)

                    # Innitial asset BUY params
                    pair = pair_dict[asset_name]
                    bid_price = get_bid_price()
                    min_size = get_minimum_size()
                    step_price = get_step_price()
                    min_trade_value = get_min_trade_value()
                    cash = get_cash()
                    pending_buy = get_pending_buy()

                    # Create BUY params
                    initial_diff = token_fix_value[asset_name]
                    buy_size = initial_diff / price
                    buy_price = bid_price - step_price

                    if cash > min_trade_value and buy_size > min_size:
                        if pending_buy == []:
                            print('Buying {} Size = {}'.format(asset_name, buy_size))
                            create_buy_order()
                            time.sleep(2)
                            if pending_buy != []:
                                print('Waiting For Order To be filled')
                                print('Buy Order Created Success, Order ID: {}'.format(pending_buy_id))
                                print('Waiting For Buy Order To be Filled')
                                time.sleep(10)

                            if pending_buy == []:
                                print("Buy order Matched")
                                print("Updateing Trade Log")
                                update_trade_log(pair)
                            else:
                                print('Buy Order is not match, Resending...')
                                pending_buy_id = get_pending_buy()[0]['id']
                                order_id = pending_buy_id
                                cancel_order()  

                        else:
                            pending_buy_id = get_pending_buy()[0]['id']
                            print("Pending BUY Order Found")
                            print("Canceling pending Order")
                            order_id = pending_buy_id
                            cancel_order()
                            if pending_buy == []:
                                print('Buy Order Matched or Cancelled')
                            else:
                                print('Buy Order is not Matched or Cancelled, Retrying')
                        print("------------------------------")
                    else:
                        print("Not Enough Balance to buy {}".format(asset_name))
                        print('Your Cash is {} // Minimum Trade Value is {}'.format(cash, min_trade_value))
                else:
                    print('{} is Already in Wallet'.format(asset_name))
                    print("------------------------------")
                    time.sleep(1)      
        
        # Rebalancing Loop
        for t in time_sequence:
            cash = get_cash()
            Time = get_time()

            print('Time : {}'.format(Time))
            print('Checking Your Asset')
            print('Your Total Asset Value is : {}'.format(total_asset))
            

            if cash > 1 and len(wallet) == len(token_name_lst) + 1:
                print('Entering Rebalance Loop')
                print("------------------------------")
                wallet = get_wallet_details()

                for item in wallet:
                    asset_name = item['coin']
                    
                    if asset_name != 'USD':
                    
                        asset_value = round(float(item['usdValue']),2)
                        fixed_value = token_fix_value[asset_name]
                        diff = abs(fixed_value - asset_value)
                        asset_amt = float(item['total'])
                        pair = pair_dict[asset_name]
                        price = get_price()
                    
                        if asset_name in token_fix_value.keys():
                            # check coin price and value
                            print('{} Price is {}'.format(asset_name, price))
                            print('{} Value is {}'.format(asset_name, asset_value))
                            
                            # Check rebalance BUY trigger
                            if asset_value < fixed_value - min_reb_size:
                                print("Current {} Value less than fix value : Rebalancing -- Buy".format(asset_name))
                                        
                                # Create trading params
                                bid_price = get_bid_price()
                                min_size = get_minimum_size()
                                step_price = get_step_price()
                                min_trade_value = get_min_trade_value()
                                cash = get_cash()
                                pending_buy = get_pending_buy()
                                
                                # Create BUY params
                                buy_size = diff / price
                                buy_price = bid_price - step_price


                                # BUY order execution
                                if cash > min_trade_value and buy_size > min_size:
                                    if pending_buy == []:
                                        print('Buying {} Size = {}'.format(asset_name, buy_size))
                                        create_buy_order()
                                        time.sleep(2)
                                        if pending_buy != []:
                                            pending_buy_id = get_pending_buy()[0]['id']
                                            print('Buy Order Created Success, Order ID: {}'.format(pending_buy_id))
                                            print('Waiting For Buy Order To be Filled')
                                            time.sleep(10)

                                        if pending_buy == []:
                                            print("Buy order Matched")
                                            update_trade_log(pair)
                                        else:
                                            print('Buy Order is not match, Resending...')
                                            pending_buy_id = get_pending_buy()[0]['id']
                                            order_id = pending_buy_id
                                            cancel_order()
                                    else:
                                        pending_buy_id = get_pending_buy()[0]['id']
                                        print("Pending Buy Order Found")
                                        print("Canceling pending Order")
                                        order_id = pending_buy_id
                                        cancel_order()
                                        if pending_buy == []:
                                            print('Buy Order Matched or Cancelled')
                                        else:
                                            print('Buy Order is not Matched or Cancelled, Retrying')
                                    print("------------------------------")
                                else:
                                    print("Not Enough Balance to buy {}".format(asset_name))
                                    print('Your Cash is {} // Minimum Trade Value is {}'.format(cash, min_trade_value))
                                    
                            # Check rebalance SELL trigger        
                            elif asset_value > fixed_value + min_reb_size:
                                print("Current {} Value more than fix value : Rebalancing -- Sell".format(asset_name))
                                
                                # Create trading params
                                bid_price = get_bid_price()
                                min_size = get_minimum_size()
                                step_price = get_step_price()
                                min_trade_value = get_min_trade_value()
                                pending_sell = get_pending_sell()
                                        
                                # Create SELL params
                                sell_size = diff / price
                                sell_price = bid_price + (3 * step_price)
                                
                                # SELL order execution
                                if diff > min_trade_value and sell_size > min_size:
                                    if pending_sell == []:
                                        print('Selling {} Size = {}'.format(asset_name, sell_size))
                                        create_sell_order()
                                        time.sleep(2)
                                        if pending_sell != []:
                                            pending_sell_id = get_pending_sell()[0]['id']
                                            print('Sell Order Created Success, Order ID: {}'.format(pending_sell_id))
                                            print('Waiting For Sell Order To be filled')
                                            time.sleep(10)

                                        if pending_sell == []:
                                            print("Sell order Matched")
                                            update_trade_log(pair)
                                        else:
                                            print('Sell Order is not match, Resending...')
                                            pending_sell_id = get_pending_sell()[0]['id']
                                            order_id = pending_sell_id
                                            cancel_order()

                                    else:
                                        pending_sell_id = get_pending_sell()[0]['id']
                                        print("Pending Order Found")
                                        print("Canceling pending Order")
                                        order_id = pending_sell_id
                                        cancel_order()
                                        if pending_sell == []:
                                            print('Sell Order Matched or Cancelled')
                                        else:
                                            print('Sell Order is not Matched or Cancelled, Retrying')
                                    print("------------------------------")
                                else:
                                    print("Not Enough Balance to sell {}".format(asset_name))
                                    print('You have {} {} // Minimum Trade Value is {}'.format(asset_name, asset_value, min_trade_value))
                                
                            else:
                                print("Current {} Value is not reach fix value yet : Waiting".format(asset_name))
                                print("------------------------------")
                                time.sleep(5)
        
        # Rebalancing Time Sequence
            print('Current Time Sequence is : {}'.format(t))
            time.sleep(t*60)

    except Exception as e:
        print('Error : {}'.format(str(e)))
        time.sleep(10)                    