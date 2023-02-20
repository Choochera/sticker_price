import Source.constants as const


class InsufficientDataException(Exception):

    def __init__(self, type: str = const.NA):
        self.messageTypeMap = {
            const.NA: 'type not provided',
            const.H_DATA: 'Not enough historical data available',
            const.QRTLY_PE: 'Not enough quarterly P/E data available',
            const.NO_FACTS: 'Error: Insufficient facts data',
            const.QRTLY_BVPS: 'Not enough quarterly BVPS data available',
            const.EPS: 'Not enough quarterly EPS data available'
            }
        self.message = self.messageTypeMap[type]
        super().__init__(self.message)
