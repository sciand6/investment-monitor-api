from flask import Flask, request, send_from_directory
from bs4 import BeautifulSoup
import requests
#from flask_cors import CORS
from yahoo_fin import stock_info
import json
import pymongo
from dotenv import load_dotenv
import os
load_dotenv()

app = Flask(__name__, static_url_path='', static_folder='build')
# CORS(app)

dbClient = pymongo.MongoClient(
    os.getenv("MONGO_URI"))

db = dbClient["screener"]


@app.route("/", defaults={'path': ''})
def serve(path):
    return send_from_directory(app.static_folder, 'index.html')


@app.route("/getStocks")
def getStocks():
    collection = db["tickers"]
    tickerCursor = collection.find()
    tickersArr = list(tickerCursor)
    prices = []
    tickers = []
    uppers = []
    lowers = []
    tickerTypes = []
    statuses = []

    for ticker in tickersArr:
        try:
            if (ticker["type"] == "stock"):
                prices.append(stock_info.get_live_price(ticker["ticker"]))
            elif (ticker["type"] == "crypto"):
                crypto = ticker["ticker"]
                cmc = requests.get(
                    f"https://coinmarketcap.com/currencies/{crypto}/")
                soup = BeautifulSoup(cmc.content, "html.parser")
                price = soup.find("div", {"class": "priceValue"}).text.replace(
                    ",", "").replace("$", "")
                prices.append(price)

            tickers.append(ticker["ticker"])
            uppers.append(ticker["upper"])
            lowers.append(ticker["lower"])
            tickerTypes.append(ticker["type"])
            statuses.append(ticker["status"])
        except Exception as ex:
            return '{"error": "That ticker is probably invalid."}'
        else:
            pass

    output = [{"ticker": t, "price": p, "upper": u, "lower": l, "type": q, "status": s}
              for t, p, u, l, q, s in zip(tickers, prices, uppers, lowers, tickerTypes, statuses)]
    return json.dumps(output)


@app.route("/addTicker", methods=["GET", "POST"])
def addTicker():
    if (request.json):
        try:
            print("TODO: Check for valid crypto and stocks")
            # stock_info.get_live_price(request.json["ticker"])
        except Exception as ex:
            return '{"error": "That ticker is probably invalid."}'
        else:
            ticker = request.json["ticker"]
            upper = request.json["upper"]
            lower = request.json["lower"]
            tickerType = request.json["type"]
            status = request.json["type"]
            tickerDict = {"ticker": ticker, "upper": upper,
                          "lower": lower, "type": tickerType, "status": status}
            collection = db["tickers"]
            inserted = collection.insert_one(tickerDict)
            return '{"success": "Ticker added successfully."}'
    else:
        return '{"error": "Error getting adding the ticker."}'


@app.route("/deleteTicker/<ticker>", methods=["DELETE"])
def deleteTicker(ticker):
    collection = db["tickers"]
    deleteQuery = {"ticker": ticker}
    collection.delete_many(deleteQuery)
    return '{"success": "Ticker deleted successfully."}'


@app.route("/updateTicker", methods=["GET", "POST"])
def updateTicker():
    if (request.json):
        try:
            print("TODO: Check for valid crypto and stocks")
            # stock_info.get_live_price(request.json["ticker"])
        except Exception as ex:
            return '{"error": "That ticker is probably invalid."}'
        else:
            collection = db["tickers"]
            ticker = request.json["ticker"]
            upper = request.json["upper"]
            lower = request.json["lower"]
            tickerType = request.json["type"]
            status = request.json["status"]
            updateQuery = {"ticker": ticker}
            updatedTicker = {
                "$set": {"ticker": ticker, "upper": upper, "lower": lower, "type": tickerType, "status": status}}
            collection.update_one(updateQuery, updatedTicker)
            return '{"success": "Ticker updated successfully."}'
    else:
        return '{"error": "Error getting updating the ticker."}'


if __name__ == '__main__':
    app.run()
