from binance.client import Client
from datetime import datetime, timedelta
import pandas as pd
from telegram.ext import Updater, CommandHandler
import time

api_key = 'YOUR_API_KEY'
api_secret = 'YOUR_SECRET_KEY'
bot_token = 'YOUR_BOT_TOKEN'

client = Client(api_key, api_secret)

def get_price_change(symbol, interval):
    klines = client.get_klines(symbol=symbol, interval=interval)
    df = pd.DataFrame(klines, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume', 'close_time', 'quote_asset_volume', 'number_of_trades', 'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    df.set_index('timestamp', inplace=True)
    price_change = (df.iloc[-1]['close'] / df.iloc[0]['close']) - 1
    return price_change

def top_gainers(bot, update):
    tickers = client.get_all_tickers()
    price_changes = {}
    for ticker in tickers:
        symbol = ticker['symbol']
        price_change_1h = get_price_change(symbol, Client.KLINE_INTERVAL_1HOUR)
        price_change_10m = get_price_change(symbol, Client.KLINE_INTERVAL_10MINUTE)
        if price_change_1h > 0:
            price_changes[symbol] = {'1hr': price_change_1h, '10m': price_change_10m}
    sorted_price_changes = sorted(price_changes.items(), key=lambda x: x[1]['1hr'], reverse=True)
    top_10_gainers = "Top 10 gainers in the past 1 hour:\n"
    for i in range(10):
        top_10_gainers += f"\n{i+1}. {sorted_price_changes[i][0]}: {sorted_price_changes[i][1]['1hr']*100:.2f}%"
    bot.send_message(chat_id=update.message.chat_id, text=top_10_gainers)

    alert_1h = "Tokens with more than 10% gain in the past 1 hour:\n"
    for symbol, price_changes in price_changes.items():
        if price_changes['1hr'] >= 0.1:
            alert_1h += f"\n{symbol}: {price_changes['1hr']*100:.2f}%"
    bot.send_message(chat_id=update.message.chat_id, text=alert_1h)

    alert_10m = "Tokens with more than 10% gain in the past 10 minutes:\n"
    for symbol, price_changes in price_changes.items():
        if price_changes['10m'] >= 0.1:
            alert_10m += f"\n{symbol}: {price_changes['10m']*100:.2f}%"
    bot.send_message(chat_id=update.message.chat_id, text=alert_10m)

updater = Updater(token=bot_token)
dispatcher = updater.dispatcher

top_gainers_handler = CommandHandler('topgainers', top_gainers)
dispatcher.add_handler(top_gainers_handler)

while True:
    updater.start_polling()
    time.sleep(60)
