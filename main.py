import hmac
import hashlib
import base64
import time
import urllib.request
import json
import tkinter as tk
import urllib.parse
import requests
from tkinter import messagebox
import threading
import sys


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

    order_type = "mkt" 
    nonce = str(int(time.time() * 1000))
    endpoint_path = "/api/v3/sendorder"
    payload = f"orderType={order_type}&symbol={trade_symbol}&side={trade_side}&size={trade_size}&nonce={nonce}"
    signature = generate_authent(api_key_private, payload, nonce, endpoint_path)

    url = "https://demo-futures.kraken.com/derivatives/api/v3/sendorder"
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
    print(entry_price)
    global position_open
    position_open = False
    print(position_open)

    def bot_loop():

        global position_open  
        global entry_price
        
        api_key_public = entry_api_key_public.get()
        api_key_private = entry_api_key_private.get()
        trade_symbol = entry_trade_symbol.get()
        trade_interval = int(entry_trade_interval.get())
        trade_size = float(entry_trade_size.get())
        trade_leverage = int(entry_trade_leverage.get())

        trade_direction = 0
        sma_values = [0.0, 0.0, 0.0]
        
        ohlc_url = 'https://api.kraken.com/0/public/OHLC?pair=%(symbol)s&interval=%(interval)d'
        api_url_base = 'https://demo-futures.kraken.com/derivatives'

        try:
            while running:
                print('Retrieving OHLC data ... ', end='')
                try:
                    api_request = urllib.request.Request(ohlc_url % {'symbol': "BTC/USD", 'interval': trade_interval})
                    api_request.add_header('User-Agent', 'Kraken trading bot example')
                    api_response = urllib.request.urlopen(api_request).read().decode()
                    api_data = json.loads(api_response)
                    print('Done' if len(api_data['error']) == 0 else f'Error ({api_data["error"]})')
                except Exception as error:
                    print(f'Failed ({error})')
                    continue

                print('Calculating SMA 20 ... ', end='')
                api_ohlc = api_data['result']["BTC/USD"] 
                api_ohlc_length = len(api_ohlc) - 1
                sma_temp = sum(float(api_ohlc[api_ohlc_length - count][4]) for count in range(1, 21)) / 20
                print('Done')

                sma_values[2] = sma_values[1]
                sma_values[1] = sma_values[0]
                sma_values[0] = sma_temp
                if sma_values[2] == 0.0:
                    print(f'Waiting {trade_interval * 60} seconds ... ')
                    time.sleep(trade_interval * 60)
                    continue
                else:
                    print(f'SMA 20 values ... {sma_values[2]} / {sma_values[1]} / {sma_values[0]}')

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

                if make_trade != 0:
                    print('Placing order/trade ... ', end='')
                    try:
                        endpoint_path = "/api/v3/sendorder"
                        url = api_url_base + endpoint_path
                        payload = f'orderType=mkt&symbol={"PI_XBTUSD"}&side={"buy" if make_trade == 1 else "sell"}&size={trade_size}&leverage={trade_leverage}'
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
                
                        if 'sendStatus' in api_data and 'orderEvents' in api_data['sendStatus'] and len(api_data['sendStatus']['orderEvents']) > 0:
                            entry_price = float(api_data['sendStatus']['orderEvents'][0]['price'])
                            position_open = True
                            trade_direction = make_trade
                            print(f'Trade placed successfully at price {entry_price}')
                        else:
                            print("Price not found in API response")

                    except Exception as error:
                        print(f'Failed ({error})')

                if position_open:
                    current_price = float(api_ohlc[-1][4])
                
                    profit_percentage = ((entry_price - current_price) / entry_price) * 100 if trade_direction == -1 else ((current_price - entry_price) / entry_price) * 100

                    print(f'Current Profit: {profit_percentage:.2f}%')

                    if profit_percentage >= 2.0:
                        print('Closing position for profit')
                        try:
                            endpoint_path = "/api/v3/sendorder"
                            url = api_url_base + endpoint_path
                            payload = f'orderType=mkt&symbol={"PI_XBTUSD"}&side={"buy" if trade_direction == -1 else "sell"}&size={trade_size}&leverage={trade_leverage}'
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
                                print('Position closed successfully')
                            else:
                                print(f"Error closing position: {api_data['error']}")

                        except Exception as error:
                            print(f'Failed to close position: {error}')

                print(f'Waiting {trade_interval * 60} seconds ... ')
                time.sleep(trade_interval * 60)

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


tk.Label(app, text="API Key Public").grid(row=0)
entry_api_key_public = tk.Entry(app)
entry_api_key_public.grid(row=0, column=1)


tk.Label(app, text="API Key Private").grid(row=1)
entry_api_key_private = tk.Entry(app, show="*")
entry_api_key_private.grid(row=1, column=1)

tk.Label(app, text="Trade Symbol").grid(row=2)
entry_trade_symbol = tk.Entry(app)
entry_trade_symbol.grid(row=2, column=1)


tk.Label(app, text="Trade Interval (minutes)").grid(row=3)
entry_trade_interval = tk.Entry(app)
entry_trade_interval.grid(row=3, column=1)


tk.Label(app, text="Auto Trade Size").grid(row=4)
entry_trade_size = tk.Entry(app)
entry_trade_size.grid(row=4, column=1)


tk.Label(app, text="Trade Leverage").grid(row=5)
entry_trade_leverage = tk.Entry(app)
entry_trade_leverage.grid(row=5, column=1)


tk.Label(app, text="Manual Trade Size").grid(row=6)
entry_manual_trade_size = tk.Entry(app)
entry_manual_trade_size.grid(row=6, column=1)

tk.Label(app, text="Trade Side").grid(row=7)
trade_side_var = tk.StringVar(value="buy")
tk.Radiobutton(app, text="Buy", variable=trade_side_var, value="buy").grid(row=7, column=1, sticky='w')
tk.Radiobutton(app, text="Sell", variable=trade_side_var, value="sell").grid(row=7, column=2, sticky='w')


test_button = tk.Button(app, text="Test API Connection", command=test_api_connection)
test_button.grid(row=8, column=0)

start_button = tk.Button(app, text="Start Bot", command=start_bot)
start_button.grid(row=9, column=0)

stop_button = tk.Button(app, text="Stop Bot", command=stop_bot)
stop_button.grid(row=9, column=1)

manual_trade_button = tk.Button(app, text="Place Manual Trade", command=place_manual_trade)
manual_trade_button.grid(row=10, column=0, columnspan=2)


app.mainloop()
