import hmac
import hashlib
import base64
import time
import urllib.request
import json
import tkinter as tk
import urllib.parse
import requests
from tkinter import messagebox,StringVar, OptionMenu
import threading
import sys
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import matplotlib.dates as mdates
from datetime import datetime
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import mplfinance as mpf
import pandas as pd


fig, ax = None, None
canvas = None



def generate_authent(api_secret, payload, nonce, endpoint_path):

    message = payload + nonce + endpoint_path
    sha256_hash = hashlib.sha256()
    sha256_hash.update(message.encode('utf-8'))
    hash_digest = sha256_hash.digest()
    secret_decoded = base64.b64decode(api_secret)
    hmac_digest = hmac.new(secret_decoded, hash_digest, hashlib.sha512).digest()
    signature = base64.b64encode(hmac_digest).decode()

    return signature

def place_manual_trade():
    api_key_public = entry_api_key_public.get()
    api_key_private = entry_api_key_private.get()
    trade_symbol = entry_trade_symbol.get()
    trade_size = float(entry_manual_trade_size.get())
    trade_side = trade_side_var.get()
    trade_leverage = int(entry_trade_leverage.get())

    api_url_base = "https://demo-futures.kraken.com/derivatives"

    endpoint_path = "/api/v3/sendorder"
    url = api_url_base + endpoint_path
    order_type = "mkt" 
    nonce = str(int(time.time() * 1000))
    payload = f"orderType={order_type}&symbol={trade_symbol}&side={trade_side}&size={trade_size}&nonce={nonce}"
    signature = generate_authent(api_key_private, payload, nonce, endpoint_path)

    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Accept': 'application/json',
        'APIKey': api_key_public,
        'Nonce': nonce,
        'Authent': signature
    }

    print("Nonce:", nonce)
    print("payload:", payload)
    print("Message (pour signature):", payload + endpoint_path)
    print("Signature:", signature)

    response = requests.request("POST", url, headers=headers, data=payload)

    print(response.text)
    print(response)



def test_api_connection():
    api_key_public = entry_api_key_public.get()
    api_key_private = entry_api_key_private.get()
    api_url_base = 'https://demo-futures.kraken.com/derivatives/api/v3'
    endpoint_path = "/api/v3/sendorder"
    
    try:
        api_path = '/tickers'
        nonce = str(int(time.time() * 1000))
        payload = f'nonce={nonce}'
        signature = generate_authent(api_key_private, payload, nonce, endpoint_path)

        url = api_url_base + api_path
        headers = {
            'APIKey': api_key_public,
            'Nonce': nonce,
            'Authent': signature
        }


        api_request = urllib.request.Request(url, headers=headers)
        api_response = urllib.request.urlopen(api_request).read().decode()
        api_data = json.loads(api_response)

        if 'error' in api_data and api_data['error']:
            messagebox.showerror("Connection Error", f"Error: {api_data['error']}")
        else:
            messagebox.showinfo("Connection Success", "API connection successful!")
    except Exception as error:
        messagebox.showerror("Connection Error", f"Failed to connect to API: {error}")


def start_bot():
    global running
    running = True

    global entry_price
    entry_price = None
    global position_open
    position_open = False
    global contract_value_in_btc
    contract_value_in_btc = float(entry_contract_value.get())

    def bot_loop():

        
        global position_open  
        global entry_price
        
        global entry_price
        global current_price
        global trade_size
        global contract_value_in_btc
        global trade_direction
        
        profit_history = []
        timestamps = []
        prices = []
        trades = []

        api_key_public = entry_api_key_public.get()
        api_key_private = entry_api_key_private.get()
        trade_symbol = entry_trade_symbol.get()
        tick_type = tick_type_var.get()
        trade_interval = int(entry_trade_interval.get())
        trade_size = float(entry_trade_size.get())
        trade_leverage = int(entry_trade_leverage.get())
        stop_loss = float(entry_stop_loss.get())
        take_profit = float(entry_take_profit.get())

        trade_direction = 0
        sma_values = [0.0, 0.0, 0.0]
        
        ohlc_url = "https://futures.kraken.com/api/charts/v1/{tick_type}/{symbol}/{interval}"
        api_url_base = 'https://demo-futures.kraken.com/derivatives'

        fig = Figure(figsize=(5, 4))
        ax = fig.add_subplot(111)

        canvas = FigureCanvasTkAgg(fig, master=graph_frame)
        canvas.get_tk_widget().grid(row=0, column=0, sticky="nsew")

        from datetime import datetime, timedelta

        def close_position():

            global position_open, entry_price, current_price, trade_size, contract_value_in_btc, trade_direction

            try:
                endpoint_path = "/api/v3/sendorder"
                url = api_url_base + endpoint_path
                payload = f'orderType=mkt&symbol={trade_symbol}&side={"buy" if trade_direction == -1 else "sell"}&size={trade_size}&leverage={trade_leverage}'
                nonce = str(int(time.time() * 1000))
                signature = generate_authent(api_key_private, payload, nonce, endpoint_path)
                headers = {
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'Accept': 'application/json',
                    'APIKey': api_key_public,
                    'Nonce': nonce,
                    'Authent': signature
                }

                response = requests.post(url, headers=headers, data=payload)
                api_data = json.loads(response.text)

                if 'error' not in api_data:
                    position_open = False
                    
                    profit_btc = (current_price - entry_price) * trade_size * contract_value_in_btc
                    profit_usd = profit_btc * current_price 
                    
                    label_profit_usd.config(text=f"${profit_usd:.2f}")
                    
                    profit_history.append(profit_usd)
            
                    text_profit_history.config(state=tk.NORMAL)
                    bg_color = "lightgreen" if profit_usd >= 0 else "lightcoral"
                    text_color = "green" if profit_usd >= 0 else "red"
                    text_profit_history.tag_config("colored_line", background=bg_color, foreground=text_color)
                    text_profit_history.insert(tk.END, f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - ${profit_usd:.2f}\n", "colored_line")
                    text_profit_history.config(state=tk.DISABLED)

                    trades.append({
                        'date': datetime.fromtimestamp(timestamps[-1]),
                        'price': current_price,
                        'type': 'close_profit' if profit_usd >= 0 else 'close_stoploss'
                    })
                    print('Position closed successfully')
                else:
                    print(f"Error closing position: {api_data['error']}")

            except Exception as error:
                print(f'Failed to close position: {error}')

        def update_chart(timestamps, prices, trades):
            if ax is None:
                print("Erreur : ax n'a pas été initialisé.")
                return

            if timestamps and prices:
                dates = [datetime.fromtimestamp(ts) for ts in timestamps]
                one_hour_ago = datetime.now() - timedelta(hours=1)
                filtered_dates = [date for date in dates if date >= one_hour_ago]
                filtered_prices = prices[-len(filtered_dates):] 

                ax.clear()

                ax.plot(filtered_dates, filtered_prices, label='Price')

                for trade in trades:
                    if trade['date'] >= one_hour_ago:
                        if trade['type'] == 'buy':
                            ax.scatter(trade['date'], trade['price'], color='green', marker='^', s=100, label='Buy')
                        elif trade['type'] == 'sell':
                            ax.scatter(trade['date'], trade['price'], color='red', marker='v', s=100, label='Sell')
                        elif trade['type'] in ['close_profit', 'close_stoploss']:
                            ax.scatter(trade['date'], trade['price'], color='blue', marker='o', s=100, label='Close')

                ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S')) 
                ax.xaxis.set_major_locator(mdates.MinuteLocator(interval=1))
                fig.autofmt_xdate()

                ax.set_title('Price Chart with Trade Decisions (Last Hour)')
                ax.set_xlabel('Time')
                ax.set_ylabel('Price')

                handles, labels = ax.get_legend_handles_labels()
                by_label = dict(zip(labels, handles))
                ax.legend(by_label.values(), by_label.keys())
            
            canvas.draw()



        try:
            while running:
                print('Retrieving OHLC data ... ', end='')
                try:
                    
                    api_request = urllib.request.Request(ohlc_url.format(symbol=trade_symbol, interval="1m",tick_type=tick_type))
                    api_request.add_header('User-Agent', 'Kraken trading bot example')
                    api_response = urllib.request.urlopen(api_request).read().decode()
                    api_data = json.loads(api_response)
    
                    if isinstance(api_data, dict) and 'candles' in api_data:
                        ohlc_data = api_data['candles']
                        print('OHLC data retrieved successfully.')

                    else:
                        print('Unexpected data structure:', api_data)
                        continue

                except Exception as error:
                    print(f'Failed ({error})')
                    continue

                print('Calculating SMA 20 ... ', end='')

                try:
    
                    if isinstance(ohlc_data, list) and len(ohlc_data) >= 20:
                        ohlc_data_length = len(ohlc_data) - 1

                        sma_temp = sum(float(ohlc_data[ohlc_data_length - count]['close']) for count in range(1, 21)) / 20
                        print('Done')

                        sma_values[2] = sma_values[1]
                        sma_values[1] = sma_values[0]
                        sma_values[0] = sma_temp

                        timestamps.append(time.time())
                        current_price = float(ohlc_data[-1]['close'])
                        prices.append(current_price)

                        if sma_values[2] == 0.0:
                            print(f'Waiting {trade_interval * 60} seconds ... ')
                            time.sleep(trade_interval * 60)
                            continue
                        else:
                            print(f'SMA 20 values ... {sma_values[2]} / {sma_values[1]} / {sma_values[0]}')

                        if position_open:
                            print("Position already open. Checking take-profit or stop-loss...")
                            profit_percentage = ((entry_price - current_price) / entry_price) * 100 if trade_direction == -1 else ((current_price - entry_price) / entry_price) * 100

                            if profit_percentage >= take_profit:
                                print('Take-profit reached. Closing position...')
                                close_position() 
                            elif profit_percentage <= -stop_loss:
                                print('Stop-loss reached. Closing position...')
                               
                                close_position()
                        else:
                            print('Trading decision ... ', end='')
                            if (sma_values[0] > sma_values[1]) and (sma_values[1] < sma_values[2]):
                                make_trade = 1
                                print('Long')
                            elif (sma_values[0] < sma_values[1]) and (sma_values[1] > sma_values[2]):
                                make_trade = -1
                                print('Short')
                            else:
                                make_trade = 0
                                print('No trade')
                    else:
                        print("Not enough OHLC data to calculate SMA.")

                except Exception as error:
                    print(f'Error in SMA calculation ({error})')
                    continue

                if make_trade != 0:
                    print('Placing order/trade ... ', end='')
                    trades.append({
                    'date': datetime.fromtimestamp(timestamps[-1]),
                    'price': current_price,
                    'type': 'buy' if make_trade == 1 else 'sell'
                    })
                    try:
                        endpoint_path = "/api/v3/sendorder"
                        url = api_url_base + endpoint_path
                        nonce = str(int(time.time() * 1000))
                        order_type = "mkt" 
                        payload = f'orderType={order_type}&symbol={trade_symbol}&side={"buy" if make_trade == 1 else "sell"}&size={trade_size}&leverage={trade_leverage}&nonce={nonce}'
                        signature = generate_authent(api_key_private, payload, nonce, endpoint_path)
                        headers = {
                            'Content-Type': 'application/x-www-form-urlencoded',
                            'Accept': 'application/json',
                            'APIKey': api_key_public,
                            'Nonce': nonce,
                            'Authent': signature
                        }

                        response = requests.post(url, headers=headers, data=payload)
                        api_data = json.loads(response.text)

                        if 'sendStatus' in api_data and 'orderEvents' in api_data['sendStatus'] and len(api_data['sendStatus']['orderEvents']) > 0:
                            entry_price = float(api_data['sendStatus']['orderEvents'][0]['price'])

                            if position_open:
                                if trade_direction == 1 and make_trade == -1: 
                                    position_open = False
                                    print('Position closed with a sell.')
                                elif trade_direction == -1 and make_trade == 1:
                                    position_open = False
                                    print('Position closed with a buy.')
                            else:
                                position_open = True
                                trade_direction = make_trade

                            print(f'Trade placed successfully at price {entry_price}')
                        else:
                            print("Price not found in API response")

                    except Exception as error:
                        print(f'Failed ({error})')
                        print("debug")

                if position_open:
                    print(current_price)
                    print("Debug Info: Entry Price:", entry_price)
                    print("Debug Info: Current Price:", current_price)
                    print("Debug Info: Position Open:", position_open)

                    profit_percentage = ((entry_price - current_price) / entry_price) * 100 if trade_direction == -1 else ((current_price - entry_price) / entry_price) * 100

                    print(f'Current Profit: {profit_percentage:.2f}%')

                    if profit_percentage >= take_profit:
                        print('Closing position for profit')
                        try:
                            close_position() 
                        except Exception as error:
                            print(f'Failed to close position: {error}')
                    elif profit_percentage <= -stop_loss:
                        print('Closing position due to Stop-Loss')
                        try:
                            close_position() 
                        except Exception as error:
                            print(f'Failed to close position: {error}')

                print(f'Waiting {trade_interval * 60} seconds ... ')
                time.sleep(trade_interval * 60)
                update_chart(timestamps, prices, trades)

                


        except KeyboardInterrupt:
            sys.exit(0)
        except Exception as error:
            print(f'Error ({error})')

    threading.Thread(target=bot_loop).start()


def stop_bot():
    global running
    running = False
    messagebox.showinfo("Info", "Bot stopped")

app = tk.Tk()
app.title("Futures Trading Bot")

running = False


tk.Label(app, text="API Key Public").grid(row=0, column=0, sticky='w', padx=5, pady=5)
entry_api_key_public = tk.Entry(app)
entry_api_key_public.grid(row=0, column=1, padx=5, pady=5)

tk.Label(app, text="API Key Private").grid(row=1, column=0, sticky='w', padx=5, pady=5)
entry_api_key_private = tk.Entry(app, show="*")
entry_api_key_private.grid(row=1, column=1, padx=5, pady=5)

tk.Label(app, text="Trade Symbol").grid(row=2, column=0, sticky='w', padx=5, pady=5)
entry_trade_symbol = tk.Entry(app)
entry_trade_symbol.insert(0, "PI_XBTUSD")
entry_trade_symbol.grid(row=2, column=1, padx=5, pady=5)

tk.Label(app, text="Trade Interval (minutes)").grid(row=3, column=0, sticky='w', padx=5, pady=5)
entry_trade_interval = tk.Entry(app)
entry_trade_interval.insert(0, "1")
entry_trade_interval.grid(row=3, column=1, padx=5, pady=5)

tk.Label(app, text="Auto Trade Size").grid(row=4, column=0, sticky='w', padx=5, pady=5)
entry_trade_size = tk.Entry(app)
entry_trade_size.insert(0, "200")
entry_trade_size.grid(row=4, column=1, padx=5, pady=5)

tk.Label(app, text="Trade Leverage").grid(row=5, column=0, sticky='w', padx=5, pady=5)
entry_trade_leverage = tk.Entry(app)
entry_trade_leverage.insert(0, "1")
entry_trade_leverage.grid(row=5, column=1, padx=5, pady=5)

tk.Label(app, text="Manual Trade Size").grid(row=6, column=0, sticky='w', padx=5, pady=5)
entry_manual_trade_size = tk.Entry(app)
entry_manual_trade_size.insert(0, "200")
entry_manual_trade_size.grid(row=6, column=1, padx=5, pady=5)

tk.Label(app, text="Manual Trade Side").grid(row=7, column=0, sticky='w', padx=5, pady=5)
trade_side_var = tk.StringVar(value="buy")
tk.Radiobutton(app, text="Buy", variable=trade_side_var, value="buy").grid(row=7, column=1, sticky='w', padx=(5, 0), pady=5)
tk.Radiobutton(app, text="Sell", variable=trade_side_var, value="sell").grid(row=7, column=1, sticky='e', padx=(0, 5), pady=5)

tk.Label(app, text="Stop-Loss (%)").grid(row=8, column=0, sticky='w', padx=5, pady=5)
entry_stop_loss = tk.Entry(app)
entry_stop_loss.insert(0, "0.04")
entry_stop_loss.grid(row=8, column=1, padx=5, pady=5)

tk.Label(app, text="Take-Profit (%)").grid(row=9, column=0, sticky='w', padx=5, pady=5)
entry_take_profit = tk.Entry(app)
entry_take_profit.insert(0, "0.04")
entry_take_profit.grid(row=9, column=1, padx=5, pady=5)

tick_type_var = StringVar(app)
tick_type_var.set("mark")  

tick_type_menu = OptionMenu(app, tick_type_var, "spot", "mark", "trade")
tick_type_menu.grid(row=10, column=1)  

tk.Label(app, text="Tick Type").grid(row=10, column=0, sticky='w', padx=5, pady=5)


tk.Label(app, text="PnL").grid(row=11, column=0, columnspan=2, sticky='n', padx=5, pady=5)
text_profit_history = tk.Text(app, height=10, width=35)
text_profit_history.grid(row=12, column=0, columnspan=2, padx=5, pady=5)
text_profit_history.config(state=tk.DISABLED)


label_profit_usd = tk.Label(app, text="$0.00")
label_profit_usd.grid(row=13, column=0, columnspan=2, sticky='n', padx=5, pady=5)

start_button = tk.Button(app, text="Start Bot", command=start_bot)
start_button.grid(row=14, column=0, padx=5, pady=5)

stop_button = tk.Button(app, text="Stop Bot", command=stop_bot)
stop_button.grid(row=14, column=1, padx=5, pady=5)

manual_trade_button = tk.Button(app, text="Place Manual Trade", command=place_manual_trade)
manual_trade_button.grid(row=15, column=0, columnspan=2, padx=5, pady=5)

test_button = tk.Button(app, text="Test API Connection", command=test_api_connection)
test_button.grid(row=16, column=0, columnspan=2, padx=5, pady=5)

graph_frame = tk.Frame(app, width=400, height=400)
graph_frame.grid(row=0, column=2, rowspan=16, padx=10, pady=10, sticky="nsew")

fig_decision = Figure(figsize=(7, 5))
ax_decision = fig_decision.add_subplot(111)
canvas_decision = FigureCanvasTkAgg(fig_decision, master=graph_frame)
canvas_decision.get_tk_widget().grid(row=0, column=0, sticky="nsew")


tk.Label(app, text="Contract Value (BTC)").grid(row=10, column=0, sticky='w', padx=5, pady=5)
entry_contract_value = tk.Entry(app)
entry_contract_value.insert(0, "0.00001694")
entry_contract_value.grid(row=17, column=1, padx=5, pady=5)


def display_static_graph():
    ax_decision.plot([1, 2, 3, 4], [1, 4, 2, 3])
    canvas_decision.draw()

display_static_graph()


app.mainloop()
