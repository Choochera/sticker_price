import Helper
import simplejson
from forex_python.converter import CurrencyRates

class dataRetriever():

    def __init__(self):
        self.helper = Helper.helper()
        self.c = CurrencyRates()

    def retrieve_quarterly_shareholder_equity(self, symbol: str) -> list[dict]:
        try:
            response = self.helper.send_SEC_api_request(symbol, "StockholdersEquity")
            data = response.json()
        except simplejson.errors.JSONDecodeError:
            try:
                response = self.helper.send_SEC_api_request(symbol, "LiabilitiesAndStockholdersEquity")
                data = response.json()
            except simplejson.errors.JSONDecodeError:
                try:
                    return self.retrieve_non_gaap_shareholder_equity(symbol)
                except:
                    raise Exception("Cannot retrieve shareholder equity data")

        qrtly_shareholder_equity = []
        for i in range(len(data['units']['USD'])):
            val = {
                data['units']['USD'][i]['end']: float(data['units']['USD'][i]['val'])
            }
            qrtly_shareholder_equity.append(val)
        return qrtly_shareholder_equity

    def retrieve_non_gaap_shareholder_equity(self, symbol: str) -> list[dict]:
        response = self.helper.retrieve_facts(symbol)
        try:
            data = response.json()
            data = data['facts']['ifrs-full']['Equity']
        except simplejson.errors.JSONDecodeError:
            raise Exception('Error retrieving facts')
        
        currency = list(data['units'].keys())[0]
        qrtly_shareholder_equity = []
        for i in range(len(data['units'][currency])):
            val = {
                data['units'][currency][i]['end']: self.c.convert(currency, 'USD', float(data['units'][currency][i]['val']))
            }
            qrtly_shareholder_equity.append(val)
        
        return qrtly_shareholder_equity

    def retrieve_quarterly_outstanding_shares(self, symbol: str) -> list[dict]:
        try:
            response = self.helper.send_SEC_api_request(symbol, "CommonStockSharesIssued")
            data = response.json()
        except simplejson.errors.JSONDecodeError:
            try:
                response = self.helper.send_SEC_api_request(symbol, "CommonStockSharesOutstanding")
                data = response.json()
            except simplejson.errors.JSONDecodeError:
                try: 
                    data = self.retrieve_non_gaap_outstanding_shares(symbol)
                except:
                    raise Exception("Shares outstanding data not available")

        qrtly_outstanding_shares = []
        for i in range(len(data['units']['shares'])):
            val = {
                data['units']['shares'][i]['end']: float(data['units']['shares'][i]['val']),
            }
            qrtly_outstanding_shares.append(val)
        return qrtly_outstanding_shares
    
    def retrieve_non_gaap_outstanding_shares(self, symbol: str) -> dict:
        response = self.retrieve_facts(symbol)
        try:
            data = response.json()
            data = data['facts']['ifrs-full']['NumberOfSharesOutstanding']
        except simplejson.errors.JSONDecodeError:
            raise Exception('Error retrieving facts')

        return data

    def retrieve_quarterly_EPS(self, symbol: str) -> list[dict]:
        quarterly_EPS = self.helper.send_SEC_api_request(symbol, 'EarningsPerShareBasic')
        try:
            data = quarterly_EPS.json()
        except simplejson.errors.JSONDecodeError:
            try:
                return self.retrieve_non_gaap_quarterly_EPS(symbol)
            except:
                raise Exception("Earnings per share data not available")

        quarterly_EPS = []
        for period in data['units']['USD/shares']:
            try:
                if 'Q' in period['frame'] or 'Q' in period['fp']:
                    val = {
                        period['end']: float(period['val']),
                    }
                    quarterly_EPS.append(val)
            except:
                #Skip values without frame 
                None

        return quarterly_EPS

    def retrieve_non_gaap_quarterly_EPS(self, symbol: str) -> list[dict]:
        response = self.helper.retrieve_facts(symbol)
        try:
            data = response.json()
            data = data['facts']['ifrs-full']['BasicEarningsLossPerShare']
        except simplejson.errors.JSONDecodeError:
            raise Exception('Error retrieving facts')

        key = list(data['units'].keys())[0]
        currency = key.replace('/shares', '')
        
        quarterly_EPS = []
        for period in data['units'][key]:
            try:
                if 'Q' in period['frame'] or 'Q' in period['fp']:
                    val = {
                        period['end']: self.c.convert(currency, 'USD', float(period['val'])),
                    }
                    quarterly_EPS.append(val)
            except:
                #Skip values without frame 
                None
        
        return quarterly_EPS

    def retrieve_fy_growth_estimate(self, symbol: str) -> float:
        return self.helper.retrieve_fy_growth_estimate(symbol)

    def retrieve_benchmark_ratio_price(self, symbol: str, benchmark: float) -> float:
        ttm_revenue: float = 0
        qrtly_revenue = []
        # Calculate ttm revenue total by adding reported revenues from last 4 quarters
        try:
            revenue = self.helper.send_SEC_api_request(symbol, 'GrossProfit').json()
        except simplejson.errors.JSONDecodeError:
            try:
                revenue = self.helper.send_SEC_api_request(symbol, 'Revenues').json()
            except simplejson.errors.JSONDecodeError:
                return 0

        for period in revenue['units']['USD']:
            try:
                if 'Q' in period['frame']:
                    qrtly_revenue.append(float(period['val']))
            except:
                #Skip values without frame 
                None
        shares_outstanding = self.helper.send_SEC_api_request(symbol, 'CommonStockSharesIssued').json()
        shares_outstanding = shares_outstanding['units']['shares'][len(shares_outstanding['units']['shares']) - 1]['val']
        ttm_revenue = sum(qrtly_revenue[-4:])

        # Equation for price based on provided market benchmark = (revenue / shares outstanding) * benchmark price-sales ratio
        return round(ttm_revenue / float(shares_outstanding), 3) * benchmark