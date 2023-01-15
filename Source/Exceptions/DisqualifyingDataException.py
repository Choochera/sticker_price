import Source.constants as const


class DisqualifyingDataException(Exception):

    def __init__(self, symbol: str = None, type: str = const.NA):
        self.symbol = symbol
        self.messageTypeMap = {
            const.NA: 'type not provided',
            const.EPS: '%s has negative annual EPS' % self.symbol,
            const.ALL_PROCESSED: 'All symbols in list have been processed'
            }
        self.message = self.messageTypeMap[type]
        super().__init__(self.message)
