from forex_python.converter import CurrencyRates
import Data_Retriever.Fact_Parser_Factory.Fact_Parser.IFact_Parser as IFact_Parser

class IFRS_Fact_Parser(IFact_Parser.IFact_Parser):

    def __init__(self, symbol: str, facts: dict):
        self.symbol = symbol
        self.c = CurrencyRates()
        self.facts = facts['facts']

    def retrieve_quarterly_shareholder_equity(self) -> list[dict]:
        try:
            data = self.facts['ifrs-full']['Equity']
        except KeyError:
            raise Exception("Cannot retrieve shareholder equity data")
        currency = list(data['units'].keys())[0]
        qrtly_shareholder_equity = []
        for i in range(len(data['units'][currency])):
            val = {
                data['units'][currency][i]['end']: self.c.convert(currency, 'USD', float(data['units'][currency][i]['val']))
            }
            qrtly_shareholder_equity.append(val)
        
        return qrtly_shareholder_equity

    def retrieve_quarterly_outstanding_shares(self) -> list[dict]:
        try:
            data = self.facts['ifrs-full']['NumberOfSharesOutstanding']
        except KeyError:
            raise Exception("Shares outstanding data not available")
        qrtly_outstanding_shares = []
        for i in range(len(data['units']['shares'])):
            val = {
                data['units']['shares'][i]['end']: float(data['units']['shares'][i]['val']),
            }
            qrtly_outstanding_shares.append(val)
        return qrtly_outstanding_shares

    def retrieve_quarterly_EPS(self) -> list[dict]:
        try:
            data = self.facts['ifrs-full']['BasicEarningsLossPerShare']
        except KeyError:
            raise Exception("Earnings per share data not available")
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

    def retrieve_benchmark_ratio_price(self, benchmark: float) -> float:
        ttm_revenue: float = 0
        qrtly_revenue = []
        # Calculate ttm revenue total by adding reported revenues from last 4 quarters
        try:
            data = self.facts['GrossProfit']
        except KeyError:
            try:
                data = self.facts['Revenue']
            except KeyError:
                print('Could not retrieve benchmark ratio price for symbol: ' + self.symbol)
                return 0

        currency = list(data['units'].keys())[0]
        for period in data['units'][currency]:
            try:
                if 'Q' in period['frame']:
                    qrtly_revenue.append(self.c.convert(currency, 'USD', float(period['val'])))
            except:
                #Skip values without frame 
                None

        try:
            shares_outstanding = self.facts['NumberOfSharesOutstanding']
        except KeyError:
            print('Could not retrieve benchmark ratio price for symbol: ' + self.symbol)
            return 0

        shares_outstanding = self.retrieve_quarterly_outstanding_shares()
        shares_outstanding = shares_outstanding['units']['shares'][len(shares_outstanding['units']['shares']) - 1]['val']
        ttm_revenue = sum(qrtly_revenue[-4:])

        # Equation for price based on provided market benchmark = (revenue / shares outstanding) * benchmark price-sales ratio
        return round(ttm_revenue / float(shares_outstanding), 3) * benchmark
