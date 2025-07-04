#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jul  4 00:25:02 2025

Consolidated stock forecast script with parallel ARIMA modeling and zoomed-in forecast plots.
"""
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jul  4 00:25:02 2025

Consolidated stock forecast script with LSTM modeling and zoomed-in forecast plots.
"""

import yfinance as yf
import datetime
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense

# Configuration
tickers = ["AAPL", "MSFT", "GOOGL", "AMZN", "META", "TSLA"]
forecast_horizon = 10
recent_days = 22
seq_len = 60  # LSTM sequence window

# Date range
end = datetime.datetime.today()
start = end - datetime.timedelta(days=365 * 2)

def process_ticker(ticker):
    try:
        # Download historical data
        df = yf.download(ticker, start=start, end=end, auto_adjust=True)
        

        # Use last ~6 months for training (~126 business days), include extra for sequence
        price_series = df['Close'].iloc[-2*126 - seq_len:].values.reshape(-1, 1)

        # Normalize
        scaler = MinMaxScaler()
        scaled_data = scaler.fit_transform(price_series)

        # Create input/output sequences
        X, y = [], []
        for i in range(seq_len, len(scaled_data) - forecast_horizon):
            X.append(scaled_data[i - seq_len:i])
            y.append(scaled_data[i:i + forecast_horizon, 0])
        X, y = np.array(X), np.array(y)

        # Build LSTM model
        model = Sequential()
        model.add(LSTM(64, return_sequences=False, input_shape=(X.shape[1], 1)))
        model.add(Dense(forecast_horizon))
        model.compile(optimizer='adam', loss='mse')

        # Train model
        model.fit(X, y, epochs=50, batch_size=16, verbose=0)

        # Forecast next 10 business days
        last_seq = scaled_data[-seq_len:]
        last_seq = last_seq.reshape(1, seq_len, 1)
        forecast_scaled = model.predict(last_seq)[0]
        forecast = scaler.inverse_transform(forecast_scaled.reshape(-1, 1)).flatten()

        # Build recent plot
        recent_history = df['Close'].iloc[-recent_days:]
        recent_dates = recent_history.index
        future_dates = pd.date_range(recent_dates[-1] + pd.Timedelta(days=1), periods=forecast_horizon, freq='B')

        # Plot
        plt.figure(figsize=(10, 6), dpi=500)
        plt.plot(recent_dates, recent_history, label='Last 1 Month', linewidth=1.5)
        plt.plot(future_dates, forecast, label='Forecast (LSTM)', linestyle='--', color='orange')
        plt.title(f'{ticker} Forecast (Zoomed View, LSTM)', fontsize=15)
        plt.xlabel('Date', fontsize=15)
        plt.ylabel('Price (USD)', fontsize=15)
        plt.legend(fontsize=15)
        plt.grid(True)
        plt.tick_params(axis='both', labelsize=15)
        plt.tight_layout()
        plt.show()

    except Exception as e:
        print(f"Error processing {ticker}: {e}")

# Run for each ticker
for t in tickers:
    process_ticker(t)
