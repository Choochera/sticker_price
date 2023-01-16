# Data Calculator
ADJ_CLOSE = 'Adj Close'
TRAILING_YEARS = 'trailing_years'
STICKER_PRICE = 'sticker_price'
SALE_PRICE = 'sale_price'
RATIO_PRICE = 'ratio_price'
QRTLY_BVPS = 'quarterly_bvps'
QRTLY_PE = 'quarterly_pe'
QRTLY_EPS = 'quarterly_eps'

# Exceptions
H_DATA = 'h_data'
QRTLY_PE = 'qrtly_PE'
EPS = 'eps'
EQUITY = 'equity'
OUTSTANDING_SHARES = 'outstanding_shares'
NA = 'N/A'
HTTP = 'http'
CONNECTING = 'connecting'
TIMEOUT = 'timeout'
REQUEST = 'request'
NO_FACTS = 'facts'
ALL_PROCESSED = 'processed'

# Data Retriever
ZACKS_URL = 'https://www.zacks.com/stock/quote/%s/detailed-estimates'
USER_AGENT = '008'
TABLE_DATA = '//td'
NEXT_FIVE_YEARS = 'Next 5 Years'

# Component Factory
GAAP = 'us-gaap'
FACTS = 'facts'
IFRS = 'ifrs-full'

# Fact Parser
HOLDERS_EQUITY = 'StockholdersEquity'
L_AND_H_EQUITY = 'LiabilitiesAndStockholdersEquity'
USD = 'USD'
UNITS = 'units'
END = 'end'
VAL = 'val'
DEI = 'dei'
COMMON_SHARES_OUTSTANDING = 'CommonStockSharesOutstanding'
COMMON_SHARES_ISSUED = 'CommonStockSharesIssued'
E_COMMON_OUTSTANDING = 'EntityCommonStockSharesOutstanding'
SHARES = 'shares'
EPS_BASIC = 'EarningsPerShareBasic'
SLASH_SHARES = '/shares'
EMPTY = ''
FRAME = 'frame'
FP = 'fp'
GROSS_PROFIT = 'GrossProfit'
REVENUES = 'Revenues'
UPPER_EQUITY = 'Equity'
NUMBER_OUTSTANDING = 'NumberOfSharesOutstanding'
E_L_PER_SHARE = 'BasicEarningsLossPerShare'
B_D_E_L_PER_SHARE = 'BasicAndDilutedEarningsLossPerShare'
REVENUE = 'Revenue'

# Helper
HELPER_USER_AGENT = 'your@email.com'
SERVICE_GET_FACTS_URL = "http://127.0.0.1:5000/getFacts/CIK%s"
SERVICE_GET_BULK_FACTS_URL = 'http://127.0.0.1:5000/getBulkFacts'
UPPER_CIK = 'CIK'
CIK_LIST = 'cikList'
LOWER_CIK = 'cik'
ZERO = '0'
PROCESSED_SYMBOLS_FILE = 'processedSymbols.txt'
APPEND = 'a'
SYMBOL_LINE = '%s\n'
STOCKLIST_FILE = 'stockList.txt'
WRITE = 'w'
SEC_CIK_URL = 'https://www.sec.gov/files/company_tickers.json'
CIK_STR = 'cik_str'
TICKER = 'ticker'
DATA_PATH = 'Service/Data'
CIKMAP_PATH = 'Service/Data/cikMap.json'
APPEND_PLUS = 'a+'
WRITE_PLUS = 'w+'

# Price Check Worker
ONE_DAY = '1d'
CLOSE = 'Close'
ON_SALE = '%s is on sale'
OUTPUT_CSV_PATH = 'Output/%s.csv'
NOT_ON_SALE = '%s is not on sale'
