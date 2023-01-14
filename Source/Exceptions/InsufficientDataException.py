import constants as const

class InsufficientDataException(Exception):

    def __init__(self, symbol: str, type: str = const.NA):
        self.symbol = symbol
        self.messageTypeMap = {
            const.NA: 'type not provided',
            const.H_DATA: """Not enough historical data available 
                        for symbol: %s""" % self.symbol,
            const.QRTLY_PE: """Not enough quarterly P/E data available
                           for symbol: %s""" % self.symbol,
            }
        self.message = self.messageTypeMap[type]
        super().__init__(self.message)
