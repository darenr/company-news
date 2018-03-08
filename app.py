from flask import Flask, render_template, request
import logging
import os
import requests
import requests_cache
from datetime import datetime

from flask_humanize import Humanize

app = Flask(__name__)
humanize = Humanize(app)

@humanize.localeselector
def get_locale():
    return 'en_EN'

requests_cache.install_cache('cache', backend='sqlite', expire_after=60*15)

def format_datetime(value, format="%Y-%m-%d"):
    return datetime.strftime(datetime.strptime(value.split('T')[0], "%Y-%m-%d"), format)

app.jinja_env.filters['datetime'] = format_datetime

def get_stock_data(symbol, news_count=50):
    j = requests.get('https://api.iextrading.com/1.0/stock/%s/batch?types=quote,logo,company,financials,relevant,news&range=6m&last=%d' % (symbol, news_count)).json()

    # postive change is up/down for easy icon rendering
    if j['quote']['change'] > 0:
        j['quote']['direction'] = 'up'
    else:
        j['quote']['direction'] = 'down'

    del j['financials']['financials'][0]['cashChange']
    del j['financials']['financials'][0]['operatingGainsLosses']

    # now get competitor news:
    if symbol.upper() == 'ORCL':
        competitors="MSFT,CRM,WDAY,IBM,INTC,SAP"
    else:
        competitors = ",".join(j['relevant']['symbols'])
    j['competitors'] = requests.get('https://api.iextrading.com/1.0/stock/market/batch?symbols=%s&types=quote,news&range=1m&last=5' % (competitors)).json()

    return j


@app.route('/')
def orcl():
    return render_template('index.html', data = get_stock_data('orcl'))

@app.route('/<string:symbol>')
def company(symbol):
    return render_template('index.html', data = get_stock_data(symbol))

if __name__ == '__main__':
    app.run(host='drace.us.oracle.com', port=8042, debug=True)
