import Source.constants as const


class DataRetrievalException(Exception):

    def __init__(
            self,
            type: str = const.NA):
        self.messageTypeMap = {
            const.NA: 'type not provided',
            const.EQUITY: "Cannot retrieve quarterly shareholder equity",
            const.OUTSTANDING_SHARES: """Cannot retrieve quarterly shareholder
                                     outstanding shares""",
            const.EPS: "Cannot retrieve earnings per share data",
            const.FACTS: "Error retrieving facts",
            const.HTTP: 'Http Error',
            const.CONNECTING: 'Error Connecting',
            const.TIMEOUT: 'Timeout Error',
            const.REQUEST: 'Request Error',
            const.H_DATA: "Download failed for all listed unprocessed symbols",
            const.LOWER_CIK: "Could not retrieve cik",
            const.INCOME: "Could not retrieve quarterly total net income",
            const.DEBT: "Could not retrieve quarterly total debt",
            const.EMPTY_FACTS: "Facts response is empty"
            }
        self.message = self.messageTypeMap[type]
        super().__init__(self.message)
