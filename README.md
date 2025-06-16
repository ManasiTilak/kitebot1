#  Kitebot

This Python project automates the following:

- Fetching access tokens for KiteConnect API
- Downloading and saving **daily trades** and **holdings**
- Uploading them to a Google Sheet
- Storing `.csv` files locally for analysis
- Generating **closed trade summaries**
- Appending **daily performance metrics** like PnL%, Batting Average, Risk/Reward ratio, Expectancy, etc.

---

## Features

### 1. **Kite Token Generator**
- Run `kite_setup.py` to log in and generate a fresh access token.
- Saves the token locally to `access_token.txt`.

### 2. **Fetch Daily Trades and Holdings**
- Run `main.py` (your main file).
- Saves daily `.csv` files:
  - `trades_DDMMYY.csv`
  - `holdings_DDMMYY.csv`
- Uploads to google sheet:
  - `Trades` tab → **appends daily**
  - `Holdings` tab → **overwrites daily**
  - `Closed Trades` tab → **based on sell trades vs average buy price**

### 3. **Closed Trade Generator**
- Aggregates all sell trades and uses average buy price from holdings.
- Produces:
  - `closed_trades_DDMMYY.csv`
  - Uploads to `Closed Trades` tab on Google Sheets.

### 4. **Performance Metrics**
- Run `get_metrics.py`
- Takes input: `closed_trades_DDMMYY.csv`
- Calculates:
  - Total Invested
  - Total PnL (₹ and %)
  - Batting Average
  - Loss Rate
  - Average Gain/Loss (₹ and %)
  - Risk:Reward Ratio
  - Expectancy
- Appends results daily to:
  - `performance_summary_by_date.csv`

---

## Setup Instructions

1. **Install Requirements**
   ```bash
   pip install kiteconnect python-dotenv google-auth google-auth-oauthlib google-api-python-client yfinance tqdm
   ```

2. **Prepare Credentials**
   - `.env` file:
     ```
     API_KEY=your_kite_api_key
     API_SECRET=your_kite_api_secret
     ```
   - `credentials.json` from Google Cloud (for Google Sheets & Drive API)

3. **Run the Token Generator**
   ```bash
   python get_access_token.py
   ```

4. **Run Daily Fetch & Upload**
   ```bash
   python main.py
   ```

5. **Run Performance Tracker**
   ```bash
   python get_metrics.py
   ```

---

## Output Files

| File | Description |
|------|-------------|
| `trades_DDMMYY.csv` | Raw trade data from Kite |
| `holdings_DDMMYY.csv` | Current holdings |
| `closed_trades_DDMMYY.csv` | Aggregated sell trades with average buy price |
| `performance_summary_by_date.csv` | Daily metrics appended |

---

## Notes

- You must re-run `kite_setup.py` when the session/token expires (which is daily).
- Your Google Sheet is named `"June"` and lives inside the Drive folder ID you configured (you can change this in the codebase itself).
- You can extend this setup to include dashboards using Looker Studio or Streamlit.

---
