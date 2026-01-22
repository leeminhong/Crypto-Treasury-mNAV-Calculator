import requests
import yfinance as yf
from bs4 import BeautifulSoup
import re
from datetime import datetime

# ==========================================
# [설정] BMNR 파라미터
# ==========================================
STOCK_TICKER = "BMNR"
# 기본값 (API 조회 실패 시 사용할 안전장치)
DEFAULT_SHARES = 454_860_000
DEFAULT_ETH_HOLDINGS = 4_168_000
PR_URL = "https://www.prnewswire.com/news/bitmine-immersion-technologies-inc./"

class DataFetcher:
    @staticmethod
    def get_market_data():
        """주가(BMNR), 이더리움(ETH) 가격, 그리고 [주식 수] 조회"""
        try:
            # 1. BMNR 객체 생성
            stock = yf.Ticker(STOCK_TICKER)

            # 주가 조회
            hist = stock.history(period="1d")
            if hist.empty:
                print("⚠️ 주가 데이터 없음")
                stock_price = None
            else:
                stock_price = float(hist['Close'].iloc[-1])

            # [핵심] 실시간 발행 주식 수 조회 (API 연동)
            shares_out = stock.info.get('sharesOutstanding')

            if shares_out is None:
                print("⚠️ 주식 수 API 조회 실패 (기본값 사용)")
                shares_out = DEFAULT_SHARES
            else:
                print(f"📡 API 주식 수 수신 성공: {shares_out:,.0f} 주")

            # 2. ETH 가격 (CoinGecko)
            url = "https://api.coingecko.com/api/v3/simple/price"
            eth_data = requests.get(url, params={"ids": "ethereum", "vs_currencies": "usd"}, timeout=5).json()
            eth_price = float(eth_data['ethereum']['usd'])

            return stock_price, eth_price, shares_out

        except Exception as e:
            print(f"⚠️ 마켓 데이터 조회 실패: {e}")
            return None, None, DEFAULT_SHARES

    @staticmethod
    def get_latest_holdings_from_news():
        """뉴스 크롤링 (실패 시 기본값 반환)"""
        try:
            headers = {'User-Agent': 'Mozilla/5.0'}
            resp = requests.get(PR_URL, headers=headers, timeout=5)
            soup = BeautifulSoup(resp.text, 'html.parser')
            text_content = soup.get_text()

            # 정규식 패턴 매칭
            match = re.search(r'Holdings.*(\d{1,3}(?:,\d{3})*)\s*ETH', text_content, re.IGNORECASE)

            if match:
                val = float(match.group(1).replace(',', ''))
                return val
            return DEFAULT_ETH_HOLDINGS # 실패 시 기본값

        except Exception:
            return DEFAULT_ETH_HOLDINGS

if __name__ == "__main__":
    print(f"🔄 시스템 가동: {datetime.now()}")
    fetcher = DataFetcher()

    # 1. 모든 데이터 실시간 수집 (주식 수 포함)
    stock_price, eth_price, real_shares = fetcher.get_market_data()
    eth_holdings = fetcher.get_latest_holdings_from_news()

    if stock_price and eth_price:
        # 2. mNAV 정밀 계산
        treasury_value = eth_holdings * eth_price

        # 주당 순자산가치 (NAV)
        nav_per_share = treasury_value / real_shares

        # mNAV 비율 (주가 / NAV)
        # 예: 1.0 = 정가, 2.0 = 2배 프리미엄
        mnav_ratio = stock_price / nav_per_share

        # 프리미엄 퍼센트 (%)
        premium_pct = (mnav_ratio - 1) * 100

        # 3. 리포트 출력
        print("\n" + "="*50)
        print(f" 📊 [BMNR] BitMine Real-Time mNAV Engine")
        print("="*50)
        print(f" 🏗️  Shares Outstanding : {real_shares:,.0f} (Live)")
        print(f" 💎 Treasury Assets    : {eth_holdings:,.0f} ETH")
        print(f" 💰 ETH Price          : ${eth_price:,.2f}")
        print("-" * 50)
        print(f" 📉 BMNR Stock Price   : ${stock_price:.2f}")
        print(f" 📊 NAV per Share      : ${nav_per_share:.2f}")
        print(f" 🚀 mNAV Ratio         : {mnav_ratio:.2f}x (Premium: {premium_pct:.2f}%)")
        print("="*50)

        # 4. 투자 시그널 (수정된 로직)
        # mNAV Ratio < 1.0 : 저평가 (Strong Buy)
        # mNAV Ratio > 2.0 : 과매수 (Strong Sell)
        if mnav_ratio < 1.0:
            print(" 👉 [BUY SIGNAL] 저평가 구간입니다. (mNAV < 1.0)")
        elif mnav_ratio > 2.0:
            print(" 👉 [SELL SIGNAL] 과매수 구간입니다. (mNAV > 2.0)")
        else:
            print(f" 👉 [HOLD] 적정 가치 구간입니다. (Current: {mnav_ratio:.2f}x)")
