import threading
import time
from datetime import datetime, timedelta
import pandas as pd
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from NSE.nse_data_fetcher.fetcher import Corperate_Announcements

_fetcher = Corperate_Announcements()

WATCHLIST_SYMBOLS = [
    "RELIANCE","TCS","HDFCBANK","INFY","ICICIBANK",
    "HINDUNILVR","ITC","SBIN","BHARTIARTL","KOTAKBANK",
    "LT","AXISBANK","BAJFINANCE","MARUTI","TITAN",
    "SUNPHARMA","ULTRACEMCO","NESTLEIND","WIPRO","HCLTECH"
]

TICKER_SYMBOLS = WATCHLIST_SYMBOLS[:15]

INDEX_SYMBOLS = [
    "NIFTY 50",
    "NIFTY BANK",
    "NIFTY IT",
    "NIFTY NEXT 50",
    "INDIA VIX"
]
SECURITIES = {
    "RELIANCE": {"name": "Reliance Industries"},
    "TCS": {"name": "Tata Consultancy"},
    "HDFCBANK": {"name": "HDFC Bank"},
    "INFY": {"name": "Infosys"},
    "ICICIBANK": {"name": "ICICI Bank"},
    "HINDUNILVR": {"name": "Hindustan Unilever"},
    "ITC": {"name": "ITC Ltd"},
    "SBIN": {"name": "State Bank of India"},
    "BHARTIARTL": {"name": "Bharti Airtel"},
    "KOTAKBANK": {"name": "Kotak Mahindra Bank"},
    "LT": {"name": "Larsen & Toubro"},
    "AXISBANK": {"name": "Axis Bank"},
    "BAJFINANCE": {"name": "Bajaj Finance"},
    "MARUTI": {"name": "Maruti Suzuki"},
    "TITAN": {"name": "Titan Company"},
    "SUNPHARMA": {"name": "Sun Pharma"},
    "ULTRACEMCO": {"name": "UltraTech Cement"},
    "NESTLEIND": {"name": "Nestle India"},
    "WIPRO": {"name": "Wipro"},
    "HCLTECH": {"name": "HCL Technologies"},
}
class _DataCache:

    def __init__(self):

        self.live_prices={}
        self.ticker_data=[]
        self.index_data=[]
        self.watchlist_df=pd.DataFrame()
        self.news_data=[]
        self.market_stats={}

        self._lock=threading.Lock()
        self._running=False

    def start(self,interval=15):

        if self._running:
            return

        self._running=True

        thread=threading.Thread(
            target=self._run_loop,
            args=(interval,),
            daemon=True
        )

        thread.start()

        print("[DataCache] Background fetcher started")

    def _run_loop(self,interval):

        while self._running:

            self._fetch_all()

            time.sleep(interval)

    def _fetch_all(self):

        print("[DataCache] Fetching NSE data",datetime.now().strftime("%H:%M:%S"))

        prices={}

        # STOCK PRICES
        for symbol in WATCHLIST_SYMBOLS:

            try:

                data=_fetcher.live_price(symbol)

                if not data:
                    continue

                last=data["lastPrice"]
                prev=data["previousClose"]

                change=last-prev
                change_pct=(change/prev)*100 if prev else 0

                prices[symbol]={

                    "symbol":symbol,
                    "price":last,
                    "open":data["open"],
                    "high":data["high"],
                    "low":data["low"],
                    "previousClose":prev,
                    "change":round(change,2),
                    "change_pct":round(change_pct,2)

                }

            except Exception as e:

                print("Price error",symbol,e)

        # INDEX DATA

        index_cards=[]

        try:

            data=_fetcher.indices()

            for row in data["data"]:

                if row["index"] in INDEX_SYMBOLS:

                    index_cards.append({

                        "name":row["index"],
                        "value":row["last"],
                        "change":row["variation"],
                        "change_pct":row["percentChange"]

                    })

        except Exception as e:

            print("Index error",e)

        ticker=[prices[s] for s in TICKER_SYMBOLS if s in prices]

        rows=[]

        for sym in WATCHLIST_SYMBOLS:

            if sym in prices:

                p=prices[sym]

                rows.append({

                    "Symbol":p["symbol"],
                    "Last":p["price"],
                    "Change":p["change"],
                    "%Chg":p["change_pct"],
                    "Open":p["open"],
                    "High":p["high"],
                    "Low":p["low"],
                    "Prev Close":p["previousClose"]

                })

        watchlist=pd.DataFrame(rows)

      # NEWS
        # NEWS (RSS)

        news_list = []

        try:

            feeds = _fetcher.daily_feeds()
            df = feeds.get("Online_announcements")

            if df is not None and not df.empty:

                for _, row in df.iterrows():

            # 🔎 DEBUG: see what RSS actually returns
                    print("RSS LINK:", row.get("link"))
                    print("TITLE:", row.get("title"))

                    link = row.get("link", "")

            # Fix relative links
                    if link and link.startswith("/"):
                        link = f"https://nsearchives.nseindia.com{link}"

                    news_list.append({
                    "timestamp": row.get("published", ""),
                    "headline": row.get("title", ""),
                    "source": "NSE",
                    "category": "RSS",
                    "link": link
                    })

                    if len(news_list) >= 10:
                        break

        except Exception as e:
            print("RSS News error:", e)
        stats={}

# EXISTING INDICES
        for idx in index_cards:

            if idx["name"]=="NIFTY 50":
                stats["nifty_50"]=idx["value"]

            if idx["name"]=="NIFTY BANK":
                stats["bank_nifty"]=idx["value"]

            if idx["name"]=="INDIA VIX":
                stats["india_vix"]=idx["value"]

# ADV / DECL + TURNOVER
        # ADV / DECL + TURNOVER
        # ADV / DECL
        try:

            adv_data = _fetcher.advance_decline()

            adv = 0
            decl = 0

            for row in adv_data.get("data", {}).get("data", []):

                if row.get("pChange",0) > 0:
                    adv += 1
                elif row.get("pChange",0) < 0:
                    decl += 1

            stats["adv_decl"] = f"{adv}/{decl}"

        except Exception as e:

            print("ADV/DECL error:",e)

# FII / DII
        # FII / DII
        # FII / DII
       # FII / DII
        try:

            data = _fetcher.fii_dii()

            if isinstance(data, list) and len(data) > 0:

                row = data[-1]

                fii = row.get("fiiBuyValue", 0)
                dii = row.get("diiBuyValue", 0)

                stats["fii_dii"] = f"{fii}/{dii}"

        except Exception as e:

            print("FII/DII error:", e)

# PUT CALL RATIO
        # PUT CALL RATIO
        # PUT CALL
       



        try:

            stats["usd_inr"]=_fetcher.usd_inr()

        except:

            stats["usd_inr"]="N/A"


        try:
            stats["gold_mcx"] = _fetcher.gold_price()
        except:
            stats["gold_mcx"] = None

        try:

            highs=_fetcher.new_highs()

            stats["new_highs"]=highs.get("high52Week",0)

        except:

            stats["new_highs"]="N/A"


        # PUT CALL
        try:

            opt = _fetcher.option_chain()

            total_put = 0
            total_call = 0

            records = opt.get("records", {}).get("data", [])

            for item in records:

                if "PE" in item:
                    total_put += item["PE"].get("openInterest", 0)

                if "CE" in item:
                    total_call += item["CE"].get("openInterest", 0)

            if total_call > 0:

                stats["put_call"] = round(total_put / total_call, 2)

        except Exception as e:

            print("PCR error:", e)

        


        try:

            stats["crude_mcx"] = _fetcher.crude_price()

        except:

            stats["crude_mcx"] = None





# NEW HIGHS
        try:
            highs=_fetcher.new_highs()

            stats["new_highs"]=highs.get("high52Week")

        except Exception as e:
            print("52week error:",e)

        with self._lock:

            self.live_prices=prices
            self.ticker_data=ticker
            self.index_data=index_cards
            self.watchlist_df=watchlist
            self.market_stats=stats
            self.news_data=news_list

        print(f"[DataCache] Updated: {len(prices)} prices | {len(index_cards)} indices | {len(news_list)} news")


_cache=_DataCache()

def start_data_cache(interval=15):

    _cache.start(interval)

def generate_ticker_data():

    with _cache._lock:
        return list(_cache.ticker_data)

def generate_index_data():

    with _cache._lock:
        return list(_cache.index_data)

def generate_watchlist():

    with _cache._lock:
        return _cache.watchlist_df.copy()

def generate_market_stats():

    with _cache._lock:
        return dict(_cache.market_stats)

def generate_news_feed(count=10):

    with _cache._lock:

        news=list(_cache.news_data)

    return news[:count]

def generate_ohlc_data(symbol: str, days: int = 30) -> pd.DataFrame:

    try:

        to_date=datetime.now()

        from_date=to_date-timedelta(days=days)

        df=_fetcher.equity_history(

            symbol=symbol,
            series="EQ",
            from_date=from_date.strftime("%d-%m-%Y"),
            to_date=to_date.strftime("%d-%m-%Y"),

        )

        if isinstance(df,tuple):

            df=df[0]

        if df is None or df.empty:

            return pd.DataFrame()

        df=df.rename(columns={

            "mtimestamp":"date",
            "chOpeningPrice":"open",
            "chTradeHighPrice":"high",
            "chTradeLowPrice":"low",
            "chClosingPrice":"close",
            "chTotTradedQty":"volume"

        })

        df["date"]=pd.to_datetime(df["date"],errors="coerce")

        for col in ["open","high","low","close","volume"]:

            df[col]=pd.to_numeric(df[col],errors="coerce")

        df=df.sort_values("date")

        live=_fetcher.live_price(symbol)

        if live:

            today=pd.Timestamp.today().normalize()

            live_row={

                "date":today,
                "open":live["open"],
                "high":live["high"],
                "low":live["low"],
                "close":live["lastPrice"],
                "volume":0

            }

            df=df[df["date"]!=today]

            df=pd.concat([df,pd.DataFrame([live_row])],ignore_index=True)

        df["sma20"]=df["close"].rolling(20).mean()
        df["sma50"]=df["close"].rolling(50).mean()

        df=df.dropna(subset=["open","high","low","close"])

        return df[[
            "date",
            "open",
            "high",
            "low",
            "close",
            "volume",
            "sma20",
            "sma50"
        ]]

    except Exception as e:

        print("OHLC error:",e)

        return pd.DataFrame()
    
    
    
    
    
    print("mmmmmmmmmmmmmmmmmmmm")