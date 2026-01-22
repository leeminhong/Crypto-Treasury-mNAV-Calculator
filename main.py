from curl_cffi import requests 
import yfinance as yf
from bs4 import BeautifulSoup
import re
from datetime import datetime
import time

# ==========================================
# [설정] BMNR 파라미터
# ==========================================
STOCK_TICKER = "BMNR"
DEFAULT_SHARES = 454_860_000
DEFAULT_ETH_HOLDINGS = 4_168_000
PR_URL = "https://www.prnewswire.com/news/bitmine-immersion-technologies-inc./"

# 안전장치용 임시 가격
FALLBACK_STOCK_PRICE = 29.35 
FALLBACK_ETH_PRICE = 3000.00

class DataFetcher:
    @staticmethod
    def get_market_data():
        """주가(BMNR), 이더리움(ETH) 가격, 그리고 [주식 수] 조회"""
        stock_price = None
        eth_price = None
        shares_out = DEFAULT_SHARES

        # -----------------------------------------------
        # 1. BMNR 주가 & 주식 수 (yfinance + curl_cffi)
        # -----------------------------------------------
        try:
            # [핵심] 블로그에서 본 그 방식! 크롬 브라우저인 척하는 세션 생성
            # impersonate="chrome" 옵션이 429 에러(차단)를 뚫어줍니다.
            session = requests.Session(impersonate="chrome")

            # yfinance에게 우리가 만든 '가짜 크롬 세션'을 강제로 쥐어줍니다.
            ticker = yf.Ticker(STOCK_TICKER, session=session)
            
            # 주가 조회
            hist = ticker.history(period="1d")
            
            if hist.empty:
                print("⚠️ Yahoo: 데이터 없음 (여전히 차단됨?)")
                stock_price = FALLBACK_STOCK_PRICE
            else:
                stock_price = float(hist['Close'].iloc[-1])
                # print(f"✅ 주가 조회 성공: ${stock_price}")

            # 주식 수 조회
            info = ticker.info
            if 'sharesOutstanding' in info and info['sharesOutstanding'] is not None:
                shares_out = info['sharesOutstanding']
                print(f"📡 API 주식 수 수신 성공: {shares_out:,.0f} 주")
            else:
                print("⚠️ 주식 수 API 조회 실패 (기본값 사용)")

        except Exception as e:
            # 혹시라도 이 방식이 막히면 에러 메시지를 보여주고 기본값을 씁니다.
            print(f"⚠️ Yahoo Finance 접속 에러: {e}")
            stock_price = FALLBACK_STOCK_PRICE

        # -----------------------------------------------
        # 2. ETH 가격 (CoinGecko)
        # -----------------------------------------------
        try:
            # 여기도 위에서 만든 session을 재활용하면 더 안전합니다.
            url = "https://api.coingecko.com/api/v3/simple/price"
            eth_data = session.get(url, params={"ids": "ethereum", "vs_currencies": "usd"}, timeout=5).json()
            eth_price = float(eth_data['ethereum']['usd'])
        except Exception as e:
            print(f"⚠️ CoinGecko 접속 실패 (임시값 사용): {e}")
            eth_price = FALLBACK_ETH_PRICE

        return stock_price, eth_price, shares_out

    @staticmethod
    def get_latest_holdings_from_news():
        """뉴스 크롤링 (curl_cffi 세션 활용)"""
        try:
            # 뉴스 검색도 크롬 브라우저인 척 접속합니다.
            session = requests.Session(impersonate="chrome")
            resp = session.get(PR_URL, timeout=10)
            soup = BeautifulSoup(resp.text, 'html.parser')
            text_content = soup.get_text()

            # 정규식 패턴 매칭
            match = re.search(r'Holdings.*(\d{1,3}(?:,\d{3})*)\s*ETH', text_content, re.IGNORECASE)

            if match:
                val = float(match.group(1).replace(',', ''))
                return val
            return DEFAULT_ETH_HOLDINGS

        except Exception:
            return DEFAULT_ETH_HOLDINGS

if __name__ == "__main__":
    print(f"🔄 시스템 가동 (curl_cffi 모드): {datetime.now()}")
    fetcher = DataFetcher()

    stock_price, eth_price, real_shares = fetcher.get_market_data()
    eth_holdings = fetcher.get_latest_holdings_from_news()

    if stock_price is None: stock_price = FALLBACK_STOCK_PRICE
    if eth_price is None: eth_price = FALLBACK_ETH_PRICE

    treasury_value = eth_holdings * eth_price
    nav_per_share = treasury_value / real_shares
    mnav_ratio = stock_price / nav_per_share
    premium_pct = (mnav_ratio - 1) * 100

    print("\n" + "="*50)
    print(f" 📊 [BMNR] BitMine Real-Time mNAV Engine")
    print("="*50)
    print(f" 🏗️  Shares Outstanding : {real_shares:,.0f}")
    print(f" 💎 Treasury Assets     : {eth_holdings:,.0f} ETH")
    print(f" 💰 ETH Price           : ${eth_price:,.2f}")
    print("-" * 50)
    print(f" 📉 BMNR Stock Price    : ${stock_price:.2f}")
    print(f" 📊 NAV per Share       : ${nav_per_share:.2f}")
    print(f" 🚀 mNAV Ratio          : {mnav_ratio:.2f}x (Premium: {premium_pct:.2f}%)")
    print("="*50)
