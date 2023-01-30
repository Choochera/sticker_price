# sticker_price
Small python program that attempts to predict stock prices by leveraging either analyst predictions or historical data regarding EPS growth, equity growth and P/E changes from the passed five years.

## Initializing:
- install python
- install postgres server and run on localhost:5432
- add postgres server username/password to init script
- run init.bat script to install dependencies
- script will take ~22 minutes to download stock market facts data and upload json files to database (this process needs only be run when the data is updated)
- run "python sticker_price.py <insert symbol> <insert symbol> ..." from sticker_price directory to process those symbols or run "python sticker_price.py" to process list of symbols within stockList.txt

## Dependencies:
- local postgres download
- python

## Requirements:
- add postgres server username/password to init script then run 
- Clear ~15gb of space for the stock data

The calculations used within this program were acquired through the book "Rule #1" authored by Phil Town. The goal is to identify underpriced stocks.
I am not a financial advisor nor am I qualified to give financial advice. The use of the this program and the reliance one gives to its outputs in terms of real
world results is entirely the responsibility of the user.
Also, Thank you!
This was a fun one to write. 
