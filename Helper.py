import requests
import pandas as pd
import lxml.html as lh

class helper():
    
    def __init__(self):
        None

    def send_SEC_api_request(self, symbol: str, element: str) -> requests.Response:
        headers = {'User-Agent': "your@email.com"}
        tickers_cik = requests.get("https://www.sec.gov/files/company_tickers.json", headers=headers)
        tickers_cik = pd.json_normalize(pd.json_normalize(tickers_cik.json(), max_level=0).values[0])
        tickers_cik["cik_str"] = tickers_cik["cik_str"].astype(str).str.zfill(10)
        cik = tickers_cik[tickers_cik["ticker"] == symbol]['cik_str']
        cik = cik.reset_index(drop = True)
        url = "https://data.sec.gov/api/xbrl/companyconcept/CIK" + cik[0] + "/us-gaap/" + element + ".json"
        response = requests.get(url, headers=headers)
        return response

    def retrieve_facts(self, symbol: str) -> requests.Response:
        headers = {'User-Agent': "your@email.com"}
        tickers_cik = requests.get("https://www.sec.gov/files/company_tickers.json", headers=headers)
        tickers_cik = pd.json_normalize(pd.json_normalize(tickers_cik.json(), max_level=0).values[0])
        tickers_cik["cik_str"] = tickers_cik["cik_str"].astype(str).str.zfill(10)
        cik = tickers_cik[tickers_cik["ticker"] == symbol]['cik_str']
        cik = cik.reset_index(drop = True)
        url = "https://data.sec.gov/api/xbrl/companyfacts/CIK" + cik[0] + ".json"
        response = requests.get(url, headers=headers)
        return response

    def retrieve_fy_growth_estimate(self, symbol: str) -> float:
        url = "https://www.zacks.com/stock/quote/" + symbol + "/detailed-estimates"

        try:
            page = requests.get(url, headers = {'User-Agent' : '008'})
            doc = lh.fromstring(page.content)
        except requests.exceptions.HTTPError as hError:
            raise Exception(str("Http Error:", hError))
        except requests.exceptions.ConnectionError as cError:
            raise Exception(str("Error Connecting:", cError))
        except requests.exceptions.Timeout as tError:
            raise Exception(str("Timeout Error:", tError))
        except requests.exceptions.RequestException as rError:
            raise Exception(str("Other Error:", rError))

        td_elements = doc.xpath('//td')

        for i in range(len(td_elements)):
            if(td_elements[i].text_content() == 'Next 5 Years'):
                return td_elements[i + 1].text_content() 
        
        return -1