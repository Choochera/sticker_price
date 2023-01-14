import constants as const

class DataRetrievalException(Exception):

    def __init__(self, symbol: str, type: str = const.NA):
        self.symbol = symbol
        self.messageTypeMap = {
            const.NA: 'type not provided',
            const.EQUITY: """Cannot retrieve quarterly shareholder
                         equity for symbol: %s""" % self.symbol,
            const.OUTSTANDING_SHARES: """Cannot retrieve quarterly shareholder
                                     outstanding shares: %s""" % self.symbol,
            }
        self.message = self.messageTypeMap[type]
        super().__init__(self.message)
