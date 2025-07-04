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
        table { border-collapse: collapse; width: 80%; margin: auto; }
        th, td { border: 1px solid #aaa; padding: 8px; text-align: center; }
        th { background-color: #333; color: white; }
        tr:nth-child(even) { background-color: #f2f2f2; }
        body { font-family: Arial; text-align: center; padding: 30px; }
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
    <div id="chart" style="width: 90%; margin: auto; height: 600px;"></div>
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
            df = yf.download(t, start=start, end=end)
            df['MA50'] = df['Close'].rolling(window=50).mean()
            df['MA200'] = df['Close'].rolling(window=200).mean()

            traces.append(go.Scatter(x=df.index, y=df['Close'], mode='lines', name=f'{t} Price'))
            traces.append(go.Scatter(x=df.index, y=df['MA50'], mode='lines', name=f'{t} MA50'))
            traces.append(go.Scatter(x=df.index, y=df['MA200'], mode='lines', name=f'{t} MA200'))
        except Exception as e:
            print(f"Error downloading historical data for {t}: {e}")

    try:
        sp500 = yf.download(benchmark, start=start, end=end)
        traces.append(go.Scatter(x=sp500.index, y=sp500['Close'], mode='lines', name='S&P 500'))
    except Exception as e:
        print(f"Error downloading S&P 500 data: {e}")

    layout = go.Layout(title='Stock Price vs Moving Averages vs S&P 500', xaxis=dict(title='Date'), yaxis=dict(title='Price (USD)'))
    fig = go.Figure(data=traces, layout=layout)
    plot_json = pio.to_json(fig)

    return render_template_string(HTML_TEMPLATE, data=data, plotly_json=plot_json)

if __name__ == "__main__":
    app.run(debug=True)
