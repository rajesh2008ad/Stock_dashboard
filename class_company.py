#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jul  3 23:39:30 2025

@author: venkata
"""
from flask import Flask, render_template_string
import yfinance as yf
import time
import datetime
import plotly.graph_objs as go
import plotly.io as pio

app = Flask(__name__)

class Company:
    def __init__(self, ticker):
        self.ticker = ticker
        self.info = yf.Ticker(ticker).info
        self.name = self.info.get("shortName", ticker)
        self.revenue = self.info.get("totalRevenue", 0) / 1e9  # in billions
        self.forward_pe = self.info.get("forwardPE", 0)

    def market_cap(self):
        return self.revenue * self.forward_pe / 1000  # in trillions

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Stock Dashboard</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            text-align: center;
            padding: 30px;
            background: linear-gradient(to bottom right, #2193b0, #f770a1);
            color: #333;
        }
        h2 {
            color: #ffffff;
            margin-bottom: 30px;
            text-shadow: 1px 1px 2px #00000050;
        }
        table {
            border-collapse: collapse;
            width: 85%;
            margin: auto;
            background-color: #ffffffcc;
            border-radius: 10px;
            overflow: hidden;
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        }
        th, td {
            padding: 12px 15px;
            text-align: center;
            border-bottom: 1px solid #ddd;
        }
        th {
            background-color: #222;
            color: white;
        }
        tr:nth-child(even) {
            background-color: #f9f9f9;
        }
        #chart {
            width: 90%;
            margin: 40px auto;
            height: 600px;
        }
    </style>
</head>
<body>
    <h2>Live Stock Dashboard</h2>
    <table>
        <tr>
            <th>Company</th>
            <th>Revenue (B USD)</th>
            <th>Forward P/E</th>
            <th>Market Cap (T USD)</th>
        </tr>
        {% for row in data %}
        <tr>
            <td>{{ row.name }}</td>
            <td>{{ row.revenue }}</td>
            <td>{{ row.forward_pe }}</td>
            <td>{{ row.market_cap }}</td>
        </tr>
        {% endfor %}
    </table>
    <div id="chart"></div>
    <script>
        var plot_data = {{ plotly_json | safe }};
        Plotly.newPlot('chart', plot_data.data, plot_data.layout);
    </script>
</body>
</html>
"""

@app.route("/")
def index():
    tickers = ["AAPL", "MSFT", "GOOGL", "AMZN", "META", "TSLA"]
    benchmark = "^GSPC"  # S&P 500 index
    data = []

    for t in tickers:
        try:
            c = Company(t)
            data.append({
                "name": c.name,
                "revenue": round(c.revenue),
                "forward_pe": round(c.forward_pe),
                "market_cap": round(c.market_cap())
            })
            time.sleep(1)
        except Exception as e:
            print(f"Error fetching {t}: {e}")

    # Historical data comparison
    end = datetime.datetime.today()
    start = end - datetime.timedelta(days=365 * 2)

    traces = []
    for t in tickers:
        try:
            df = yf.download(t, start=start, end=end, auto_adjust=False)
            if not df.empty and 'Close' in df.columns:
                #df = df.dropna(subset=['Close'])
                df['MA50'] = df['Close'].rolling(window=50).mean()
                df['MA200'] = df['Close'].rolling(window=200).mean()

                traces.append(go.Scatter(x=df.index, y=df['Close'], mode='lines', name=f'{t} Price'))
                traces.append(go.Scatter(x=df.index, y=df['MA50'], mode='lines', name=f'{t} MA50'))
                traces.append(go.Scatter(x=df.index, y=df['MA200'], mode='lines', name=f'{t} MA200'))
            else:
                print(f"No valid data for {t}")
        except Exception as e:
            print(f"Error downloading historical data for {t}: {e}")

    try:
        sp500 = yf.download(benchmark, start=start, end=end)
        if not sp500.empty and 'Close' in sp500.columns:
            sp500 = sp500.dropna(subset=['Close'])
            traces.append(go.Scatter(x=sp500.index, y=sp500['Close'], mode='lines', name='S&P 500'))
    except Exception as e:
        print(f"Error downloading S&P 500 data: {e}")

    layout = go.Layout(title='Stock Price vs Moving Averages vs S&P 500', xaxis=dict(title='Date'), yaxis=dict(title='Price (USD)'))
    fig = go.Figure(data=traces, layout=layout)
    plot_json = pio.to_json(fig)

    return render_template_string(HTML_TEMPLATE, data=data, plotly_json=plot_json)

if __name__ == "__main__":
    app.run(debug=True)
