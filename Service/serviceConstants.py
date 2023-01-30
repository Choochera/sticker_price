# Misc
DB_USERNAME_KEY = 'db_username'
DB_PASSWORD_KEY = 'db_password'
HOST = 'localhost'
DATABASE_NAME = 'postgres'
USER_AGENT_VALUE = 'XYZ/3.0'
DATA_DIRECTORY = 'Data'
CIK_LIST = 'cikList'
DEFAULT_DB_USERNAME = 'postgres'
DEFAULT_DB_PASSWORD = 'password'
DEFAULT_DB_NAME = 'postgres'
POST = 'POST'

# Queries
GET_PROCESSED_CIK_QUERY = 'SELECT cik from facts'
CREATE_FACTS_TABLE_QUERY = """CREATE TABLE IF NOT EXISTS facts (
                            cik varchar(13) not null primary key,
                            data jsonb
                        );"""
INSERT_DATA_QUERY = """INSERT INTO facts (cik, data)
                     values('%s', (select * from to_jsonb('%s'::JSONB)))"""
GET_DATA_QUERY = "SELECT data FROM facts where cik = '%s'"
APPEND_CIK_QUERY = " or cik = '%s'"

# Urls
EDGAR_URL = "https://www.sec.gov/Archives/edgar"
DATA_ZIP_PATH = "/daily-index/xbrl/companyfacts.zip"
