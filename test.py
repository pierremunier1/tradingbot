import requests

# Define the URL
symbol = "PI_XBTUSD"  # Bitcoin/USD perpetual futures contract
interval = "1m"  # 1-minute interval
ohlc_url = f'https://futures.kraken.com/api/charts/v1/trade/{symbol}/{interval}'

# Make the API request
response = requests.get(ohlc_url)
ohlc_data = response.json()

# Print the data to inspect it
print(ohlc_data)
