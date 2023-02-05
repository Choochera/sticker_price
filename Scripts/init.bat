cd ../
set db_username=postgres
set db_password=password
setx db_username postgres
setx db_password password
pip install psycopg2
pip install requests
pip install pandas
pip install simplejson
pip install yfinance
pip install forex_python
pip install flask
pip install pycodestyle
python Service/migrate_db.py
