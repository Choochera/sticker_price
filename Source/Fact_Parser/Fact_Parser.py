from forex_python.converter import CurrencyRates
import Source.Fact_Parser.IFact_Parser as IFP
import Source.constants as const
import Source.Exceptions.DataRetrievalException as DRE
import Source.ComponentFactory as CF
import json


class Fact_Parser(IFP.IFact_Parser):

    def __init__(self, symbol: str, facts: dict, taxonomy: str = const.GAAP):
        self.symbol = symbol
        self.c = CurrencyRates()
        self.facts = facts[const.FACTS]
        self.helper = CF.ComponentFactory.getHelperObject()
        self.taxonomy = taxonomy

    def retrieve_quarterly_data(self, factsKeys: list[str], taxonomyType: str = const.GAAP, deiFactsKeys: list[str] = []) -> list[dict]:
        data = self.__retrieve_requested_data(
            factsKeys=factsKeys,
            deiFactsKeys=deiFactsKeys,
            taxonomyType=taxonomyType
        )
        hasStartDate = self.__checkHasStartDate(data)
        
        if (hasStartDate):
            quarterly_data = self.__populate_quarterly_data_with_start_date(data)
        else:
            quarterly_data = self.__populate_quarterly_data_without_start_date(data)

        if (len(quarterly_data) == 0):
            raise DRE.DataRetrievalException(const.NA)

        return quarterly_data

    def __retrieve_requested_data(self, factsKeys: list[str], deiFactsKeys: list[str], taxonomyType: str) -> dict:
        data = None
        i = 0
        while (data is None and i < len(factsKeys)):
            try:
                data = self.facts[taxonomyType][factsKeys[i]]
            except KeyError:
                data = None
            i += 1
        if (data is None):
            i = 0
            while (data is None and i < len(deiFactsKeys)):
                try:
                    data = self.facts[const.DEI][deiFactsKeys[i]]
                except KeyError:
                    pass
                i += 1
        if (data is None):
            raise DRE.DataRetrievalException(const.NA)
        return data

    def __checkHasStartDate(self, data: dict) -> bool:
        quarter = data[const.UNITS][list(data[const.UNITS].keys())[0]][0]
        try: 
            return quarter[const.START] is not None
        except KeyError:
            return False
            
    def __populate_quarterly_data_with_start_date(self, data: dict) -> list:
        quarterly_data = []
        period_end_dates: list[str] = []
        key = list(data[const.UNITS].keys())[0]
        currency = key.replace(const.SLASH_SHARES, const.EMPTY)
        for period in data[const.UNITS][key]:
            try:
                if (
                    period[const.END] not in period_end_dates and
                    self.helper.days_between(
                        period[const.START],
                        period[const.END]
                    ) < 105
                ):
                    amount = float(period[const.VAL])
                    amount = self.c.convert(currency, const.USD, amount)
                    val = {
                        period[const.END]: amount
                    }
                    quarterly_data.append(val)
                    period_end_dates.append(period[const.END])
            except KeyError:
                # Skip values without frame
                None
        return quarterly_data
        
    def __populate_quarterly_data_without_start_date(self, data: dict) -> list:
        quarterly_data = []
        isShares = False
        key = list(data[const.UNITS].keys())[0]
        currency = key.replace(const.SLASH_SHARES, const.EMPTY)
        for period in data[const.UNITS][currency]:
            amount: float = float(period[const.VAL])
            if (not isShares):
                try:          
                    amount = self.c.convert(currency, const.USD, amount)
                except Exception as e:
                    if (str(e) == const.INVALID_CURRENCY_MESSAGE):
                        amount: float = float(period[const.VAL])
                        isShares = True
            val = {
                period[const.END]: amount
            }
            quarterly_data.append(val)
        return quarterly_data
