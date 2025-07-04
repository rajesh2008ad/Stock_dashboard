#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jul  4 00:25:02 2025

Consolidated stock forecast script with parallel ARIMA modeling and zoomed-in forecast plots.
"""

import yfinance as yf
import datetime
import matplotlib.pyplot as plt
import pandas as pd
from pmdarima import auto_arima
from joblib import Parallel, delayed

# Configuration
tickers = ["AAPL", "MSFT", "GOOGL", "AMZN", "META", "TSLA"]
benchmark = "^GSPC"
forecast_horizon = 100  # Next 100 trading days
recent_days = 90  # Past ~3 months of trading days

# Date range
end = datetime.datetime.today()
start = end - datetime.timedelta(days=365 * 5)

def process_ticker(ticker):
    try:
        # Download data
        df = yf.download(ticker, start=start, end=end, auto_adjust=True)
        if df.empty or 'Close' not in df.columns:
            print(f"No valid data for {ticker}")
            return

        #df = df.dropna(subset=['Close'])
        df['MA50'] = df['Close'].rolling(window=50).mean()
        df['MA200'] = df['Close'].rolling(window=200).mean()

        # Plot full history with moving averages
        plt.figure(figsize=(10, 6), dpi=500)
        plt.plot(df.index, df['Close'], label=f'{ticker} Close', linewidth=1.5)
        plt.plot(df.index, df['MA50'], label='50-day MA', linestyle='--')
        plt.plot(df.index, df['MA200'], label='200-day MA', linestyle='--')
        plt.title(f'{ticker} Price with Moving Averages', fontsize=15)
        plt.xlabel('Date', fontsize=15)
        plt.ylabel('Price (USD)', fontsize=15)
        plt.legend(fontsize=15)
        plt.grid(True)
        plt.tick_params(axis='both', labelsize=15)
        plt.tight_layout()
        plt.show()

        # Train ARIMA model
        print(f"Training ARIMA model for {ticker}...")
        model = auto_arima(df['Close'].iloc[-30:], seasonal=False, stepwise=True,
                           suppress_warnings=True, error_action='ignore', trace=False)
        forecast, conf_int = model.predict(n_periods=forecast_horizon, return_conf_int=True)

        # Extract past month and create future dates
        recent_history = df['Close'].iloc[-recent_days:]
        recent_dates = recent_history.index
        future_dates = pd.date_range(recent_dates[-1] + pd.Timedelta(days=1),
                                     periods=forecast_horizon, freq='B')

        # Zoomed forecast plot
        plt.figure(figsize=(10, 6), dpi=500)
        plt.plot(recent_dates, recent_history, label='Last 3 Months', linewidth=1.5)
        plt.plot(future_dates, forecast, label='Forecast (Next 2 Weeks)', linestyle='--', color='red')
        plt.fill_between(future_dates, conf_int[:, 0], conf_int[:, 1],
                         color='red', alpha=0.2, label='95% Confidence Interval')
        plt.title(f'{ticker} Forecast (Zoomed View)', fontsize=15)
        plt.xlabel('Date', fontsize=15)
        plt.ylabel('Price (USD)', fontsize=15)
        plt.legend(fontsize=15)
        plt.grid(True)
        plt.tick_params(axis='both', labelsize=15)
        plt.tight_layout()
        plt.show()

    except Exception as e:
        print(f"Error processing {ticker}: {e}")

# Run all tickers in parallel
for t in tickers:
     process_ticker(t)

# Plot S&P 500 for reference
try:
    sp500 = yf.download(benchmark, start=start, end=end, auto_adjust=True)
    if not sp500.empty and 'Close' in sp500.columns:
        plt.figure(figsize=(10, 6), dpi=500)
        plt.plot(sp500.index, sp500['Close'], label='S&P 500', color='black')
        plt.title('S&P 500 Index (Close Price)', fontsize=15)
        plt.xlabel('Date', fontsize=15)
        plt.ylabel('Price (USD)', fontsize=15)
        plt.legend(fontsize=15)
        plt.grid(True)
        plt.tight_layout()
        plt.show()
except Exception as e:
    print(f"Error downloading S&P 500: {e}")
