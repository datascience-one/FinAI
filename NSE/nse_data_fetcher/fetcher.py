
"""
fetcher.py
==========

This module provides the `Corperate_Announcements` class, a high-level interface
for fetching, parsing, and managing corporate disclosure data from the
**National Stock Exchange of India (NSE)**.

The class integrates multiple data endpoints including corporate announcements,
annual reports, board meetings, financial results, insider trading disclosures,
and more. Each endpoint is fetched via decorated methods that automatically:

1. Build API URLs dynamically (`@fetch_data`)
2. Record request and response timestamps and save outputs as JSON (`@track_time`)
3. Return processed results as pandas DataFrames ready for further analysis or
   database storage.

Key Features
-------------
- Fetch corporate announcements, annual reports, board meetings, buybacks, governance reports, etc.
- Retrieve daily RSS feeds from NSE for updates.
- Handle data fetching, parsing, and encoding (including cookies and headers).
- Save or append processed data to SQL databases through `DatabaseHandler`.
- Support historical equity data download in chunks (automatic pagination).

Classes
--------
Corperate_Announcements
    Provides a suite of methods to retrieve and process various types of NSE
    corporate data and historical stock data.

Dependencies
-------------
- requests
- pandas
- feedparser
- sqlalchemy
- datetime
- urllib.parse
"""
from .utils import track_time
import urllib.parse
import re
import os
import json
import datetime
import requests
import feedparser
import pandas as pd
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import create_engine, MetaData

from .utils import track_time
from .db_operations import DatabaseHandler



@track_time
class Corperate_Announcements:
    def __init__(self, curl_headers=None, config_file=None):
        """
        Initialize the Corperate_Announcements class with default or provided headers and config file.

        Args:
            curl_headers (str, optional): Custom curl headers for making requests. Defaults to a predefined set.
            config_file (str, optional): Path to the configuration file for database operations. Defaults to None.
        """

        self.curl_headers = curl_headers or ''' -H "authority: beta.nseindia.com" -H "cache-control: max-age=0" -H "dnt: 1" -H "upgrade-insecure-requests: 1" -H "user-agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.117 Safari/537.36" -H "sec-fetch-user: ?1" -H "accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9" -H "sec-fetch-site: none" -H "sec-fetch-mode: navigate" -H "accept-encoding: gzip, deflate, br" -H "accept-language: en-US,en;q=0.9,hi;q=0.8" --compressed'''
        self.config_file = config_file
        self.session = requests.Session()
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                          "(KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": "https://www.nseindia.com/",
            "Connection": "keep-alive",
        }
        # warm cookies
        self.session.get("https://www.nseindia.com", headers=self.headers, timeout=15)
        self.session.get("https://www.nseindia.com/api/option-chain-indices?symbol=NIFTY",
                         headers=self.headers, timeout=10)

        self.db_handler = DatabaseHandler(config_file)
        self.rss_urls = [
                          "https://nsearchives.nseindia.com/content/RSS/Online_announcements.xml",
                          "https://nsearchives.nseindia.com/content/RSS/Annual_Reports.xml",
                          "https://nsearchives.nseindia.com/content/RSS/Board_Meetings.xml",
                          "https://nsearchives.nseindia.com/content/RSS/brsr.xml",
                          "https://nsearchives.nseindia.com/content/RSS/Corporate_action.xml",
                          "https://nsearchives.nseindia.com/content/RSS/Corporate_Governance.xml",
                          "https://nsearchives.nseindia.com/content/RSS/Daily_Buyback.xml",
                          "https://nsearchives.nseindia.com/content/RSS/Financial_Results.xml",
                          "https://nsearchives.nseindia.com/content/RSS/Insider_Trading.xml",
                          "https://nsearchives.nseindia.com/content/RSS/Investor_Complaints.xml",
                          "https://nsearchives.nseindia.com/content/RSS/Offer_Documents.xml",
                          "https://nsearchives.nseindia.com/content/RSS/Related_Party_Trans.xml",
                          "https://nsearchives.nseindia.com/content/RSS/Sast_Regulation29.xml",
                          "https://nsearchives.nseindia.com/content/RSS/Sast_Regulation31.xml",
                          "https://nsearchives.nseindia.com/content/RSS/Sast_ReasonForEncumbrance.xml",
                          "https://nsearchives.nseindia.com/content/RSS/Secretarial_Compliance.xml",
                          "https://nsearchives.nseindia.com/content/RSS/Share_Transfers.xml",
                          "https://nsearchives.nseindia.com/content/RSS/Shareholding_Pattern.xml",
                          "https://nsearchives.nseindia.com/content/RSS/Statement_Of_Deviation.xml",
                          "https://nsearchives.nseindia.com/content/RSS/Unitholding_Patterns.xml",
                          "https://nsearchives.nseindia.com/content/RSS/Voting_Results.xml",
                          "https://nsearchives.nseindia.com/content/RSS/Circulars.xml"
                      ]
        self.default_historical_params = {
            "functionName": "getHistoricalTradeData",
            "excel": "true"
        }


        self.api_endpoints = {
              "corporate_company_announcements": "https://www.nseindia.com/api/corporate-announcements",
              "corporate_announcements": "https://www.nseindia.com/api/corporate-announcements",
              "corporate_annual_reports": "https://www.nseindia.com/api/annual-reports",
              "corporate_board_meetings": "https://www.nseindia.com/api/corporate-board-meetings",
              "corporate_brsr": "https://www.nseindia.com/api/corporate-bussiness-sustainabilitiy",
              "corporate_actions": "https://www.nseindia.com/api/corporates-corporateActions",
              "corporate_governance": "https://www.nseindia.com/api/corporate-governance-master",
              "corporate_daily_buy_back": "https://www.nseindia.com/api/corporates-daily-buyback",
              "corporate_financial_results": "https://www.nseindia.com/api/corporates-financial-results",
              "corporate_insider_trading": "https://www.nseindia.com/api/corporates-pit",
              "corporate_investor_complaints": "https://www.nseindia.com/api/investor-complaints",
              "corporate_related_party_transactions": "https://www.nseindia.com/api/related-party-transactions-master",
              "corporate_regulation_29": "https://www.nseindia.com/api/corporate-sast-reg29",
              "corporate_regulation_31": "https://www.nseindia.com/api/corporate-pledgedata-sast3132",
              "corporate_reason_for_encumbrance": "https://www.nseindia.com/api/corp-encumbrance",
              "corporate_secretarial_compliance": "https://www.nseindia.com/api/secretarial-camp",
              "corporate_share_transfers": "https://www.nseindia.com/api/corpreg7",
              "corporate_shareholding_patterns": "https://www.nseindia.com/api/corporate-share-holdings-master",
              "corporate_statement_of_deviation": "https://www.nseindia.com/api/statement-deviation-master",
              "corporate_unitholding_patterns": "https://www.nseindia.com/api/corporate-unit-holdings-master",
              "corporate_voting_results": "https://www.nseindia.com/api/corporate-voting-results",
              "circulars": "https://www.nseindia.com/api/circulars",
              "historical": "https://www.nseindia.com/api/NextApi/apiClient/GetQuoteApi",

        }

    def _call_api(self, endpoint_key, **kwargs):
        """
        Centralized API caller.
        Builds URL dynamically using endpoint key and keyword arguments.
        """

        base_url = self.api_endpoints.get(endpoint_key)

        if not base_url:
            raise ValueError(f"Endpoint '{endpoint_key}' not found")


        query_string = urllib.parse.urlencode(kwargs)
        url = f"{base_url}?{query_string}"


        return self._nsefetch(url)


    def custom_daily_feeds(self, data, headers=None):
        """
        Fetches and parses daily RSS feed data from the provided URL.

        Args:
            data (str): The URL of the RSS feed to fetch data from.
            headers (dict, optional): Custom headers to use for the request. Defaults to a generic User-Agent.

        Returns:
            pd.DataFrame: A DataFrame containing the parsed RSS feed data.
            dict: A dictionary with an error message if an exception occurs.
        """
        if headers is None:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
        try:
            response = requests.get(data, headers=headers)
            response.raise_for_status()  # Raises HTTPError for bad responses (4xx, 5xx)

            feed = feedparser.parse(response.content)
            if feed.bozo:  # Checks if there was a problem parsing the feed
                raise ValueError(f"Malformed feed data: {feed.bozo_exception}")
            parsed_data = []
            for entry in feed.entries:
                parsed_data.append({
                    'title': entry.title,
                    'link': entry.link,
                    'published': entry.published,
                    'summary': entry.summary
                })

            df = pd.DataFrame(parsed_data)
            return df

        except requests.exceptions.RequestException as e:
            return {"error": f"Request error: {e}"}
        except ValueError as e:
            return {"error": f"Parsing error: {e}"}
        except Exception as e:
            return {"error": f"An unexpected error occurred: {e}"}

    def daily_feeds(self):
        """
        Fetches and processes all pre-defined RSS feeds, returning the data in a dictionary of DataFrames.

        Returns:
            dict: A dictionary where keys are base names of RSS feed URLs, and values are DataFrames containing the feed data.
        """
        results = {}
        for rss_url in self.rss_urls:
            df = self.custom_daily_feeds(rss_url)
            base_name = os.path.splitext(os.path.basename(rss_url))[0]
            results[base_name] = df
        return results


    def _nsefetch(self, url):
        try:
            self.session.get("https://www.nseindia.com", headers=self.headers, timeout=10)
            r = self.session.get(url, headers=self.headers, timeout=15)
            r.raise_for_status()

            try:
                return r.json()
            except ValueError:
                raise ValueError(f"Invalid JSON response. Snippet:\n{r.text[:300]}")

        except requests.exceptions.RequestException as e:
            raise ValueError(f"Request error fetching NSE data: {e}")


    def corporate_company_announcements(self, **kwargs):
        """
        Fetches and processes corporate company announcements data from the NSE.

        Args:
            data (dict): The JSON data returned from the NSE API.

        Returns:
            pd.DataFrame: A DataFrame containing the processed announcements data.
        """
        data = self._call_api("corporate_company_announcements", **kwargs)

        df = pd.DataFrame(data).rename(columns={
            'symbol': 'SYMBOL',
            'sm_name': 'COMPANY NAME',
            'desc': 'SUBJECT',
            'attchmntText': 'DETAILS',
            'an_dt': 'BROADCAST DATE/TIME',
            'sort_date': 'RECEIPT',
            'exchdisstime': 'DISSEMINATION',
            'difference': 'DIFFERENCE',
            'attchmntFile': 'ATTACHMENT',
            'sm_isin': 'ISIN'
        }).dropna(axis=1, how='all')
        desired_order = ['SYMBOL', 'COMPANY NAME', 'SUBJECT', 'ISIN', 'DETAILS',
                         'BROADCAST DATE/TIME', 'RECEIPT', 'DISSEMINATION',
                         'DIFFERENCE', 'ATTACHMENT']
        return df[desired_order], "corporate_company_announcements"

    def corporate_announcements(self, **kwargs):
        """
        Fetches and processes general corporate announcements data from the NSE.

        Args:
            data (dict): The JSON data returned from the NSE API.

        Returns:
            pd.DataFrame: A DataFrame containing the processed announcements data.
        """
        data = self._call_api("corporate_announcements", **kwargs)

        df = pd.DataFrame(data)
        return df, "corporate_announcements"

    def corporate_annual_reports(self, **kwargs):
        """
        Fetches and processes annual reports data from the NSE.

        Args:
            data (dict): The JSON data returned from the NSE API.

        Returns:
            pd.DataFrame: A DataFrame containing the processed annual reports data.
        """
        data = self._call_api("corporate_annual_reports", **kwargs)

        df = pd.DataFrame(data['data']).rename(columns={
            'companyName': 'COMPANY NAME',
            'fromYr': 'FROM YEAR',
            'toYr': 'TO YEAR',
            'fileName': 'FILE'
        })
        return df, "corporate_annual_reports"

    def corporate_board_meetings(self, **kwargs):
        """
        Fetches and processes corporate board meetings data from the NSE.

        Args:
            data (dict): The JSON data returned from the NSE API.

        Returns:
            pd.DataFrame: A DataFrame containing the processed board meetings data.
        """
        data = self._call_api("corporate_board_meetings", **kwargs)

        df = pd.DataFrame(data).rename(columns={
                'bm_symbol': 'SYMBOL',
                'bm_date': 'MEETING DATE',
                'bm_purpose': 'PURPOSE',
                'bm_desc': 'DETAILS',
                'sm_indusrty': 'INDUSTRY',
                'bm_timestamp': 'BROADCAST DATE/TIME',
                'sm_name': 'COMPANY NAME',
                'sm_isin': 'ISIN',
                'attachment': 'ATTACHMENT',
                'diff': 'TIME TAKEN',
                'sysTime': 'EXCHANGE DISSEMINATION TIME'
                })
        desired_order = ['SYMBOL', 'COMPANY NAME', 'INDUSTRY', 'ISIN', 'PURPOSE', 'DETAILS', 'MEETING DATE', 'ATTACHMENT', 'BROADCAST DATE/TIME', 'EXCHANGE DISSEMINATION TIME', 'TIME TAKEN']
        df = df[desired_order]
        return df, "corporate_board_meetings"

    def corporate_brsr(self, **kwargs):
        """
        Fetches and processes business sustainability reports data from the NSE.

        Args:
            data (dict): The JSON data returned from the NSE API.

        Returns:
            pd.DataFrame: A DataFrame containing the processed business sustainability reports data.
        """
        data = self._call_api("corporate_brsr", **kwargs)

        df = pd.DataFrame(data['data'])
        df = df.rename(columns={'symbol': 'SYMBOL',
                          'companyName': 'COMPANY NAME',
                          'fyFrom': 'FROM YEAR',
                          'fyTo': 'TO YEAR',
                          'attachmentFile': 'ATTACHMENT',
                          'xbrlFile': '**XBRL',
                          'submissionDate': 'ORIGINAL SUBMISSION DATE',
                          'revisionDate': 'LATEST REVISION DATE'})
        return df, "corporate_brsr"

    def corporate_actions(self, **kwargs):
        """
        Fetches and processes corporate actions data from the NSE.

        Args:
            data (dict): The JSON data returned from the NSE API.

        Returns:
            pd.DataFrame: A DataFrame containing the processed corporate actions data.
        """
        data = self._call_api("corporate_actions", **kwargs)

        df = pd.DataFrame(data)
        df = df.rename(columns={'symbol': 'SYMBOL',
                                'series': 'SERIES',
                                'comp': 'COMPANY NAME',
                                'isin': 'ISIN',
                                'subject': 'PURPOSE',
                                'faceVal': 'FACE VALUE',
                                'exDate': 'EX-DATE',
                                'recDate': 'RECORD DATE',
                                'bcStartDate': 'BOOK CLOSURE START DATE',
                                'bcEndDate': 'BOOK CLOSURE END DATE',
                                })
        df = df[['SYMBOL', 'SERIES', 'COMPANY NAME', 'ISIN', 'PURPOSE', 'FACE VALUE', 'EX-DATE', 'RECORD DATE', 'BOOK CLOSURE START DATE', 'BOOK CLOSURE END DATE']]
        return df, "corporate_actions"

    def corporate_governance(self, **kwargs):
        """
        Fetches and processes corporate governance data from the NSE.

        Args:
            data (dict): The JSON data returned from the NSE API.

        Returns:
            pd.DataFrame: A DataFrame containing the processed corporate governance data.
        """
        data = self._call_api("corporate_governance", **kwargs)

        df = pd.DataFrame(data['data'])
        df = df.rename(columns = {'symbol': 'SYMBOL',
                                  'name': 'COMPANY NAME',
                                  'date':	'QUARTER END DATE',
                                  'desc':	'DETAILS',
                                  'xbrl':	'XBRL FILE LINK **',
                                  'cgTimeStamp':	'BROADCAST DATE & TIME'})
        df = df[['SYMBOL', 'COMPANY NAME', 'QUARTER END DATE', 'DETAILS', 'XBRL FILE LINK **', 'BROADCAST DATE & TIME']]
        return df, "corporate_governance"

    def corporate_daily_buy_back(self, **kwargs):
        """
        Fetches and processes daily buyback data from the NSE.

        Args:
            data (dict): The JSON data returned from the NSE API.

        Returns:
            pd.DataFrame: A DataFrame containing the processed daily buyback data.
        """
        data = self._call_api("corporate_daily_buy_back", **kwargs)

        df = pd.DataFrame(data['data'])
        df = df.rename(columns = {'symbol': 'SYMBOL',
                                  'sm_name': 'COMPANY NAME',
                                  'desc':	'SUBJECT',
                                  'attchmntFile': 'ATTACHMENT',
                                  'an_dt': 'BROADCAST DATE/TIME'})
        df = df[['SYMBOL', 'COMPANY NAME', 'SUBJECT', 'ATTACHMENT', 'BROADCAST DATE/TIME']]
        return df, "corporate_daily_buy_back"

    def corporate_financial_results(self, **kwargs):
        """
        Fetches and processes corporate financial results data from the NSE.

        Args:
            data (dict): The JSON data returned from the NSE API.

        Returns:
            pd.DataFrame: A DataFrame containing the processed financial results data.
        """
        data = self._call_api("corporate_financial_results", **kwargs)

        df = pd.DataFrame(data)
        df = df.rename(columns = {'symbol': 'SYMBOL',
                                  'companyName': 'COMPANY NAME',
                                  'audited': 'AUDITED / UNAUDITED',
                                  'cumulative': 'CUMULATIVE / NON-CUMULATIVE',
                                  'financialYear': 'FINANCIAL YEAR',
                                  'indAs': 'IND AS/ NON IND AS',
                                  'period': 'PERIOD',
                                  'fromDate': 'PERIOD START',
                                  'toDate': 'PERIOD ENDED',
                                  'relatingTo': 'RELATING TO',
                                  'xbrl': '** XBRL'})
        df = df[['SYMBOL', 'COMPANY NAME', 'AUDITED / UNAUDITED', 'CUMULATIVE / NON-CUMULATIVE', 'FINANCIAL YEAR', 'IND AS/ NON IND AS', 'PERIOD', 'PERIOD START', 'PERIOD ENDED', 'RELATING TO', '** XBRL']]
        return df, "corporate_financial_results"

    def corporate_insider_trading(self, **kwargs):
        """
        Fetches and processes insider trading data from the NSE.

        Args:
            data (dict): The JSON data returned from the NSE API.

        Returns:
            pd.DataFrame: A DataFrame containing the processed insider trading data.
        """
        data = self._call_api("corporate_insider_trading", **kwargs)

        df = pd.DataFrame(data['data'])
        df = df.rename(columns = {'symbol': 'SYMBOL',
                                  'company': 'COMPANY NAME',
                                  'anex': 'REGULATION',
                                  'acqName': 'Name of the Acquirer/ Disposer',
                                  'secType': 'Type of Security',
                                  'secAcq': 'No. of Securities',
                                  'tdpTransactionType': 'Acquisition/ Disposal',
                                  'date': 'Broadcast Date/Time',
                                  'xbrl': 'XBRL File Link**'})
        df = df[['SYMBOL', 'COMPANY NAME', 'REGULATION', 'Name of the Acquirer/ Disposer', 'Type of Security', 'No. of Securities', 'Acquisition/ Disposal', 'Broadcast Date/Time', 'XBRL File Link**']]
        return df, "corporate_insider_trading"

    def corporate_investor_complaints(self, **kwargs):
        """
        Fetches and processes investor complaints data from the NSE API.

        Args:
            data (dict): The JSON data returned from the NSE API.

        Returns:
            pd.DataFrame: A DataFrame containing the processed investor complaints data.
        """
        data = self._call_api("corporate_investor_complaints", **kwargs)

        df = pd.DataFrame(data['data'])
        df = df.rename(columns = {'companyName': 'COMPANY NAME',
                                  'date': 'For Quarter Ending',
                                  'complBeg': 'Pending at the begining of quarter',
                                  'complRecv':'Received during the quarter',
                                  'complDisp': 'Disposed off during the quarter',
                                  'complUnres': 'Remaining unresolved at the end of quarter',
                                  'xbrl': 'XBRL file link **',
                                  'broadcastDate': 'BROADCAST DATE/TIME'
                                  })
        df = df[['COMPANY NAME', 'For Quarter Ending', 'Pending at the begining of quarter', 'Received during the quarter', 'Disposed off during the quarter', 'Remaining unresolved at the end of quarter', 'XBRL file link **', 'BROADCAST DATE/TIME']]
        return df, "corporate_investor_complaints"

    def corporate_related_party_transactions(self, **kwargs):
        """
        Fetches and processes related party transactions data from the NSE API.

        Args:
            data (dict): The JSON data returned from the NSE API.

        Returns:
            pd.DataFrame: A DataFrame containing the processed related party transactions data.
        """
        data = self._call_api("corporate_related_party_transactions", **kwargs)

        df = pd.DataFrame(data['data'])
        return df, "corporate_related_party_transactions"

    def corporate_regulation_29(self, **kwargs):
        """
        Fetches and processes corporate Regulation 29 data from the NSE API.

        Args:
            data (dict): The JSON data returned from the NSE API.

        Returns:
            pd.DataFrame: A DataFrame containing the processed Regulation 29 data.
        """
        data = self._call_api("corporate_regulation_29", **kwargs)

        df = pd.DataFrame(data['data'])
        return df, "corporate_regulation_29"

    def corporate_regulation_31(self, **kwargs):
        """
        Fetches and processes corporate Regulation 31 data (Disclosure of encumbered shares.) from the NSE API.

        Args:
            data (dict): The JSON data returned from the NSE API.

        Returns:
            pd.DataFrame: A DataFrame containing the processed Regulation 31 data.
        """
        data = self._call_api("corporate_regulation_31", **kwargs)

        df = pd.DataFrame(data['data'])
        return df, "corporate_regulation_31"

    def corporate_reason_for_encumbrance(self, **kwargs):
        """
        Fetches and processes the reasons for corporate encumbrance data from the NSE API.

        Args:
            data (dict): The JSON data returned from the NSE API.

        Returns:
            pd.DataFrame: A DataFrame containing the processed encumbrance data.
        """
        data = self._call_api("corporate_reason_for_encumbrance", **kwargs)

        df = pd.DataFrame(data['data'])
        return df, "corporate_reason_for_encumbrance"

    def corporate_secretarial_compliance(self, **kwargs):
        """
        Fetches and processes secretarial compliance data from the NSE API.

        Args:
            data (dict): The JSON data returned from the NSE API.

        Returns:
            pd.DataFrame: A DataFrame containing the processed secretarial compliance data.
        """
        data = self._call_api("corporate_secretarial_compliance", **kwargs)

        df = pd.DataFrame(data)
        return df, "corporate_secretarial_compliance"

    def corporate_share_transfers(self, **kwargs):
        """
        Fetches and processes corporate share transfers data from the NSE API.

        Args:
            data (dict): The JSON data returned from the NSE API.

        Returns:
            pd.DataFrame: A DataFrame containing the processed share transfers data.
        """
        data = self._call_api("corporate_share_transfers", **kwargs)

        df = pd.DataFrame(data)
        return df, "corporate_share_transfers"

    def corporate_shareholding_patterns(self, **kwargs):
        """
        Fetches and processes corporate shareholding patterns data from the NSE API.

        Args:
            data (dict): The JSON data returned from the NSE API.

        Returns:
            pd.DataFrame: A DataFrame containing the processed shareholding patterns data.
        """
        data = self._call_api("corporate_shareholding_patterns", **kwargs)

        df = pd.DataFrame(data)
        return df, "corporate_shareholding_patterns"

    def corporate_statement_of_deviation(self, **kwargs):
        """
        Fetches and processes corporate statement of deviation data from the NSE API.

        Args:
            data (dict): The JSON data returned from the NSE API.

        Returns:
            pd.DataFrame: A DataFrame containing the processed statement of deviation data.
        """
        data = self._call_api("corporate_statement_of_deviation", **kwargs)

        df = pd.DataFrame(data['data'])
        return df, "corporate_statement_of_deviation"

    def corporate_unitholding_patterns(self, **kwargs):
        """
        Fetches and processes corporate unitholding patterns data from the NSE API.

        Args:
            data (dict): The JSON data returned from the NSE API.

        Returns:
            pd.DataFrame: A DataFrame containing the processed unitholding patterns data.
        """
        data = self._call_api("corporate_unitholding_patterns", **kwargs)

        df = pd.DataFrame(data['data'])
        return df, "corporate_unitholding_patterns"



    def corporate_voting_results(self, **kwargs):
        """
        Fetch corporate voting results from the NSE API.

        Args:
            data (list): JSON list returned from the NSE API.

        Returns:
            pd.DataFrame: A DataFrame containing voting results.
        """
        data = self._call_api("corporate_voting_results", **kwargs)

        df = pd.DataFrame(data)      # <-- FIX (data is already a list)
        return df, "corporate_voting_results"


    def circulars(self, **kwargs):
        """
        Fetches and processes circulars data from the NSE API.

        Args:
            data (dict): The JSON data returned from the NSE API.

        Returns:
            pd.DataFrame: A DataFrame containing the processed circulars data.
        """
        data = self._call_api("circulars", **kwargs)

        df = pd.DataFrame(data['data'])
        return df, "circulars"

    def live_price(self, symbol):
        base_url = "https://www.nseindia.com/api/quote-equity"
        params = {"symbol": symbol}
        query = urllib.parse.urlencode(params)
        url = f"{base_url}?{query}"
        data = self._nsefetch(url)
        if "priceInfo" in data:
          return {
              "symbol": symbol,
              "lastPrice": data["priceInfo"].get("lastPrice"),
              "open": data["priceInfo"].get("open"),
              "high": data["priceInfo"].get("intraDayHighLow", {}).get("max"),
              "low": data["priceInfo"].get("intraDayHighLow", {}).get("min"),
              "previousClose": data["priceInfo"].get("previousClose")
              }
        return None
    def indices(self):

        url = "https://www.nseindia.com/api/allIndices"

        return self._nsefetch(url)

    def equity_history_virgin(self, symbol, series, from_date, to_date, **kwargs):

        base_url = self.api_endpoints["historical"]

        params = self.default_historical_params.copy()
        # Required default parameters
        params.update({
            "symbol": symbol,
            "series": series,
            "fromDate": from_date,
            "toDate": to_date
        })

        # for future
        params.update(kwargs)

        # Convert dict to url
        query_string = urllib.parse.urlencode(params)

        url = f"{base_url}?{query_string}"

        payload = self._nsefetch(url)

        if isinstance(payload, dict) and "data" in payload:
            return pd.DataFrame(payload["data"])
        else:
            return pd.DataFrame(payload)


    def equity_history(self, symbol, series, from_date, to_date):

        from_date = datetime.datetime.strptime(from_date, "%d-%m-%Y")
        to_date = datetime.datetime.strptime(to_date, "%d-%m-%Y")

        total = pd.DataFrame()
        current_start = from_date

        while current_start <= to_date:
            current_end = min(current_start + datetime.timedelta(days=40), to_date)

            start_str = current_start.strftime("%d-%m-%Y")
            end_str   = current_end.strftime("%d-%m-%Y")

            chunk = self.equity_history_virgin(symbol, series, start_str, end_str)

            if not chunk.empty:
                total = pd.concat([total, chunk], ignore_index=True)

            current_start = current_end + datetime.timedelta(days=1)


        return total.reset_index(drop=True),"equity_history"



    def save_or_append_to_db(self, df, table_name, append=False):
        """
        Saves or appends a DataFrame to the database based on the specified table name.

        Args:
            df (pd.DataFrame): The DataFrame to be saved or appended.
            table_name (str): The name of the table in the database.
            append (bool, optional): If True, appends the data to the existing table. If False, creates a new table. Defaults to False.
        """
        self.db_handler.save_or_append_to_db(df, table_name, append)


    def market_status(self):
        url = "https://www.nseindia.com/api/marketStatus"
        return self._nsefetch(url)

    def fii_dii(self):
        url = "https://www.nseindia.com/api/fiidiiTradeReact"
        return self._nsefetch(url)

    def option_chain(self):
        url = "https://www.nseindia.com/api/option-chain-indices?symbol=NIFTY"
        return self._nsefetch(url)

    def new_highs(self):
        url = "https://www.nseindia.com/api/live-analysis-52Week"
        return self._nsefetch(url)
    def advance_decline(self):

        url = "https://www.nseindia.com/api/equity-stockIndices?index=NIFTY%2050"

        return self._nsefetch(url)
    def usd_inr(self):

        url="https://api.exchangerate-api.com/v4/latest/USD"

        data=requests.get(url).json()

        return data["rates"]["INR"]
    def gold_price(self):

        try:

            url = "https://api.gold-api.com/price/XAU"

            r = requests.get(url, timeout=10)

            data = r.json()

            return data.get("price")

        except Exception as e:

            print("Gold API error:", e)

            return None
        
    def crude_price(self):

        try:

            url = "https://api.exchangerate.host/convert?from=USD&to=INR"

            r = requests.get(url, timeout=10)

            data = r.json()

            return data.get("result")

        except Exception as e:

            print("Crude API error:", e)

            return None
        
    def option_chain(self):

        self.session.get("https://www.nseindia.com", headers=self.headers)

        url = "https://www.nseindia.com/api/option-chain-indices?symbol=NIFTY"

        return self._nsefetch(url)