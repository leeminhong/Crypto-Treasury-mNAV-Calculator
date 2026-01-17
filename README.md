# Crypto-Treasury-mNAV-Calculator

### Overview
This project calculates the **Real-Time mNAV (Modified Net Asset Value)** for public companies holding cryptocurrency treasuries (e.g., BMNR).

It automatically fetches financial data to determine if the stock is trading at a **Premium** or **Discount** relative to its underlying crypto assets.

### Features
* **Live Data:** Fetches Stock price (`yfinance`) and Ethereum price (`CoinGecko`).
* **Auto-Update:** Scrapes the latest ETH holdings from press releases using `BeautifulSoup`.
* **Accuracy:** Adjusts for real-time `Shares Outstanding` to prevent dilution errors.
* **Visualization:** Plots historical Premium/Discount trends.

### Logic
* **mNAV** = (Crypto Holdings × Current Crypto Price) / Shares Outstanding
* **Premium(%)** = (Stock Price / mNAV - 1) × 100

### How to Run
1. Install dependencies:
   ```bash
   pip install yfinance requests beautifulsoup4 matplotlib pandas

2. Run the Script
    ```bash
   python main.py

