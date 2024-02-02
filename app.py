import matplotlib
matplotlib.use('Agg')
from flask import Flask, render_template, request , send_file

import pandas as pd
import pandas_datareader.data as web
import matplotlib.pyplot as plt
import io
import base64

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        from zipline.api import order_target, record, symbol
        from zipline.finance import commission, slippage
        from zipline import run_algorithm
        # Get input values from the form
        symbol_input = request.form['symbol']
        short_mavg_input = int(request.form['short_mavg'])
        long_mavg_input = int(request.form['long_mavg'])
        stock_quantity_input = int(request.form['stock_quantity'])
        start_year_input = int(request.form['start_year_simulation'])
        end_year_input = int(request.form['end_year_simulation'])
        capital_input = float(request.form['capital'])

        def initialize(context):
            context.i = 0
            context.asset = symbol('NFTY_3')


        def handle_data(context, data):
            # Skip first 300 days to get full windows
            context.i += 1
            if context.i < 300:
                return

            # Compute averages
            # data.history() has to be called with the same params
            # from above and returns a pandas dataframe.
            short_mavg = data.history(context.asset, 'price', bar_count=short_mavg_input, frequency="1d").mean()
            long_mavg = data.history(context.asset, 'price', bar_count=long_mavg_input, frequency="1d").mean()

            # Trading logic
            if short_mavg > long_mavg:
                # order_target orders as many shares as needed to
                # achieve the desired number of shares.
                order_target(context.asset, stock_quantity_input)
            elif short_mavg < long_mavg:
                order_target(context.asset, 0)

            # Save values for later inspection
            record(NFTY_3=data.current(context.asset, 'price'),
                short_mavg=short_mavg,
                long_mavg=long_mavg)


        def analyze(context, perf):
            fig = plt.figure()
            ax1 = fig.add_subplot(211)
            perf.portfolio_value.plot(ax=ax1)
            ax1.set_ylabel('portfolio value in $')

            ax2 = fig.add_subplot(212)
            perf['NFTY_3'].plot(ax=ax2)
            perf[['short_mavg', 'long_mavg']].plot(ax=ax2)
            perf.to_csv("performance.csv",index=False)
            perf_trans = perf.loc[[t != [] for t in perf.transactions]]
            buys = perf_trans.loc[[t[0]['amount'] > 0 for t in perf_trans.transactions]]
            sells = perf_trans.loc[
                [t[0]['amount'] < 0 for t in perf_trans.transactions]]
            ax2.plot(buys.index, perf.short_mavg.loc[buys.index],
                    '^', markersize=10, color='m')
            ax2.plot(sells.index, perf.short_mavg.loc[sells.index],
                    'v', markersize=10, color='k')
            ax2.set_ylabel('price in $')
            plt.legend(loc=0)
            plt.savefig('./static/portfolio_value_chart.png')
            plt.close()

        start = pd.Timestamp("2020")
        end = pd.Timestamp("2025")
        perf = run_algorithm(
            # start=pd.Timestamp(f"{start_year_input}-01-01"),
            # end=pd.Timestamp(f"{end_year_input}-1-31"),
            start=start,
            end=end,
            initialize=initialize,
            handle_data=handle_data,
            capital_base=capital_input,
            bundle="nfty-bundle",
            data_frequency="daily",
        )
        fig = plt.figure()
        ax1 = fig.add_subplot(211)
        perf.portfolio_value.plot(ax=ax1)
        ax1.set_ylabel('portfolio value in $')

        ax2 = fig.add_subplot(212)
        perf['NFTY_3'].plot(ax=ax2)
        perf[['short_mavg', 'long_mavg']].plot(ax=ax2)
        perf_data = pd.DataFrame({
        'period_open': perf.period_open,
        'period_close': perf.period_close,
        'pnl': perf.pnl,
        'portfolio_value': perf.portfolio_value,
        'longs_count': perf.longs_count,
        'transactions': perf.transactions,
        'shorts_count': perf.shorts_count,
        'positions': perf.positions,
        'starting_cash': perf.starting_cash,
        'ending_cash': perf.ending_cash,
        'capital_used': perf.capital_used,
        'orders': perf.orders,
        'returns': perf.returns,
        'sortino': perf.sortino,
        'sharpe': perf.sharpe,
        'max_drawdown': perf.max_drawdown,
        'max_leverage': perf.max_leverage,
        'NFTY_3': perf['NFTY_3']
    })
        perf.to_csv("metric.csv",index=False)
        perf_data.to_csv("performance.csv",index=False)
        perf_trans = perf.loc[[t != [] for t in perf.transactions]]
        buys = perf_trans.loc[[t[0]['amount'] > 0 for t in perf_trans.transactions]]
        sells = perf_trans.loc[
            [t[0]['amount'] < 0 for t in perf_trans.transactions]]
        ax2.plot(buys.index, perf.short_mavg.loc[buys.index],
                '^', markersize=10, color='m')
        ax2.plot(sells.index, perf.short_mavg.loc[sells.index],
                'v', markersize=10, color='k')
        ax2.set_ylabel('price in $')
        plt.legend(loc=0)
        plt.savefig('./static/portfolio_value_chart.png')
        plt.close()

        # Plot the performance chart
        # performance_chart = plot_performance(result)

        # Get the last row of portfolio_value
        capital = capital_input
        last_portfolio_value = perf.portfolio_value.iloc[-1]
        pnl = perf.portfolio_value.iloc[-1] - capital_input

        #period_open period_close pnl portfolio_value longs_count transactions shorts_count positions starting_cash ending_cash capital_used orders returns sortino sharpe max_drawdown max_leverage NFTY_3
        return render_template('index.html', last_portfolio_value=last_portfolio_value,capital=capital,pnl=pnl,perf_data=perf_data)

    return render_template('index.html')

@app.route('/download_csv')
def download_csv():
    return send_file('performance.csv', as_attachment=True)

@app.route('/download_image')
def download_image():
    return send_file('static/portfolio_value_chart.png', as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)