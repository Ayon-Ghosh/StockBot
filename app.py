from flask import Flask, request, make_response
#from pandas.util.testing import assert_frame_equal
import os, json
import pandas as pd
from datetime import datetime, timedelta
#import pandas as pd
import pandas_datareader.data as web
from fuzzywuzzy import process
import requests
from flask_cors import CORS,cross_origin
import matplotlib.pyplot as plt
import smtplib
from email.message import EmailMessage
from config_reader import read_config
#import warnings

app = Flask(__name__)

# geting and sending response to dialogflow
@app.route('/webhook', methods=['POST'])
@cross_origin()
def webhook():
    req = request.get_json(silent=True, force=True)

    print("Request:")
    print(json.dumps(req))

    res = processRequest(req)

    res = json.dumps(res)
    print(res)
    r = make_response(res)
    r.headers['Content-Type'] = 'application/json'
    return r


def processRequest(req):
    intent_query = result.get("intent")
    intent_name = intent_query.get("displayName")
    print(intent_name)

    if intent_name == 'stockDetails':
        result = req.get("queryResult")
        parameters = result.get("parameters")
        company_name = req.get("company_name")
        res = get_stock_details(company_name)
        return res
    else:
        res = sendEmail()
        return res


def sendEmail():
    if request.json['EmailId'] is not None:
        symbols = symbol_list()
        save_attachment(symbols)

        msg = EmailMessage()
        msg['To'] = request.json['EmailId']
        readConfig = read_config()
        msg['From'] = readConfig['SENDER_EMAIL']
        pswd = readConfig['PASSWORD']
        msg.set_content(readConfig['EMAIL_BODY'])
        msg['Subject'] = readConfig['EMAIL_SUBJECT']
        list_of_files = os.listdir()
        if 'full_figure.pdf' in list_of_files:
            files = ['full_figure.pdf']
            for file in files:
                with open(file, 'rb') as f:
                    file_data = f.read()
                    file_name = f.name
                msg.add_attachment(file_data, maintype='application', subtype='octet-stream', filename=file_name)
            with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
                smtp.login(msg['From'], pswd)
                smtp.send_message(msg)

        emptyTargetFiles(list_of_files)
        speech = 'You will soon receive an email with an attached document that shows the performance of the stocks you asked about. Caio'
        return {
            "fulfillmentText": speech,
            "displayText": speech
        }


# All Helper functions below --------------**********************************
# processing the request from Lex
def get_stock_details(company_name):
    end_date = datetime.today()
    start_date = end_date - timedelta(weeks=52)
    end = end_date.strftime('%Y-%m-%d')
    start = start_date.strftime('%Y-%m-%d')
    r = requests.get('https://api.iextrading.com/1.0/ref-data/symbols')
    stockList = r.json()
    stock_symbol = process.extractOne(company_name, stockList)[0]['symbol']
    with open('temp.csv', 'a+') as temp_file:
        temp_file.write(stock_symbol)
        temp_file.write('\n')
    df = web.DataReader(stock_symbol, 'yahoo', start, end)
    df_MAX = df['High'].max()
    df_MIN = df['Low'].min()
    speech = f'Today the details of {stock_symbol} are high: {round(df.High.tail(1)[0], 2)} and low: {round(df.Low.tail(1)[0], 2)}. The 52 week high is {round(df_MAX, 2)}.The 52 week low is {round(df_MIN, 2)}. You can either ask about stock details of another company or share your email id so we can send you the consolidated report. '
    return {
    "fulfillmentText": speech,
    "displayText": speech
     }


# writing the company names from different POST request in a temp file

def symbol_list():
    symbol_list = []
    with open('temp.csv', 'r') as fread:
        for line in fread:
            line = line.strip()
            symbol_list.append(line)
    return symbol_list


# creating dataframe of each stocks for last 52 weeks, plotting it, and saving as PDF in the same folder
def save_attachment(symbol_list):
    counter = 0
    fig = plt.figure()
    fig, axs = plt.subplots(len(symbol_list), figsize=(16, 10))
    end_date = datetime.today()
    start_date = end_date - timedelta(weeks=52)
    end = end_date.strftime('%Y-%m-%d')
    start = start_date.strftime('%Y-%m-%d')
    for i in symbol_list:
        df = web.DataReader(i, 'yahoo', start, end)
        df = df[['High', 'Low']]
        axs[counter].set_title(i)
        axs[counter].plot(df)
        counter = counter + 1
    fig.savefig('full_figure.pdf')


# deleting files .pdf and temp.csv after the job is done

def emptyTargetFiles(files_list):
    if len(files_list) > 0:
        for i in files_list:
            if 'pdf' in i or 'csv' in i:
                os.remove(i)
            else:
                continue


if __name__ == '__main__':
    app.run(debug=True)
    # port = int(os.getenv('PORT', 5000))
    # print("Starting app on port %d" % port)
    # app.run(host='0.0.0.0', port=port)
