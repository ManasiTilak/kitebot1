from kiteconnect import KiteConnect
from dotenv import load_dotenv
import os
import csv
from datetime import datetime
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

'''
Currently has 2 functions : Get trades and get holdings. 
You get these files locally. 
These files are also uploaded to June google sheet inside "Kite data" folder
Holdings are overwritten and trades are added to the sheet.
'''

# === CONFIG ===
load_dotenv()
API_KEY = os.getenv("API_KEY")
ACCESS_TOKEN = open("access_token.txt", "r").read().strip()
FOLDER_ID = "1QCVqb9uULQhnqdmXKsNCHcEJdVITIt_Q"
SPREADSHEET_NAME = "June"
SCOPES = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]

# === GOOGLE SHEETS SERVICES ===
def get_services():
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    else:
        flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
        creds = flow.run_local_server(port=0)
        with open("token.json", "w") as token:
            token.write(creds.to_json())
    return build("sheets", "v4", credentials=creds), build("drive", "v3", credentials=creds)

# === CREATE/GET SPREADSHEET ===
def get_or_create_spreadsheet(sheets, drive):
    query = f"name = '{SPREADSHEET_NAME}' and mimeType='application/vnd.google-apps.spreadsheet' and '{FOLDER_ID}' in parents"
    result = drive.files().list(q=query, fields="files(id)").execute().get("files", [])
    if result:
        return result[0]["id"]
    meta = {"name": SPREADSHEET_NAME, "mimeType": "application/vnd.google-apps.spreadsheet", "parents": [FOLDER_ID]}
    sheet = drive.files().create(body=meta, fields="id").execute()
    return sheet["id"]

# === UPLOAD TO SHEET (overwrite for holdings, append for trades) ===
def upload_to_sheet(sheets, sheet_id, rows, sheet_name, overwrite=False):
    if not rows:
        print(f"⚠️ No data to upload to {sheet_name}")
        return

    if overwrite:
        # Clear existing data first
        sheets.spreadsheets().values().clear(
            spreadsheetId=sheet_id,
            range=f"{sheet_name}"
        ).execute()
        print(f"🧹 Cleared {sheet_name} tab before upload.")

    body = {"values": rows}
    sheets.spreadsheets().values().append(
        spreadsheetId=sheet_id,
        range=f"{sheet_name}!A1",
        valueInputOption="RAW",
        insertDataOption="INSERT_ROWS",
        body=body
    ).execute()
    print(f"✅ Uploaded to {sheet_name} tab in Google Sheet")


# === FETCH AND SAVE TRADES ===
def get_trades(kite, filename, date_str):
    trades = kite.trades()
    headers = ["date", "tradingsymbol", "transaction_type", "average_price", "quantity"]
    rows = [[date_str, t["tradingsymbol"], t["transaction_type"], t["average_price"], t["quantity"]] for t in trades]
    with open(filename, mode="w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(headers)
        writer.writerows(rows)
    print(f"✅ Saved trades to {filename}")
    return [headers] + rows

# === FETCH AND SAVE HOLDINGS ===
def get_holdings(kite, filename, date_str):
    holdings = kite.holdings()
    headers = ["date", "tradingsymbol", "quantity", "average_price", "last_price", "pnl", "product", "exchange"]
    rows = [
        [
            date_str,
            h["tradingsymbol"],
            h["quantity"],
            h["average_price"],
            h["last_price"],
            h["pnl"],
            h["product"],
            h["exchange"]
        ]
        for h in holdings
    ]
    with open(filename, mode="w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(headers)
        writer.writerows(rows)
    print(f"✅ Saved holdings to {filename}")
    return [headers] + rows

def generate_closed_trades(today_str, sheets, sheet_id):
    trades_file = f"trades_{datetime.now().strftime('%d%m%y')}.csv"
    holdings_file = f"holdings_{datetime.now().strftime('%d%m%y')}.csv"
    output_file = f"closed_trades_{datetime.now().strftime('%d%m%y')}.csv"

    if not os.path.exists(trades_file) or not os.path.exists(holdings_file):
        print("⚠️ Trades or holdings file not found.")
        return

    # Read trades
    with open(trades_file, newline="") as f:
        trade_reader = csv.DictReader(f)
        sell_trades = [row for row in trade_reader if row["transaction_type"] == "SELL"]

    # Group by tradingsymbol to calculate avg sell price and total qty
    sell_summary = {}
    for row in sell_trades:
        symbol = row["tradingsymbol"]
        price = float(row["average_price"])
        qty = int(row["quantity"])
        if symbol not in sell_summary:
            sell_summary[symbol] = {"total_qty": 0, "total_value": 0}
        sell_summary[symbol]["total_qty"] += qty
        sell_summary[symbol]["total_value"] += price * qty

    for symbol in sell_summary:
        s = sell_summary[symbol]
        s["avg_sell_price"] = round(s["total_value"] / s["total_qty"], 2)

    # Read holdings to get avg buy price
    with open(holdings_file, newline="") as f:
        holdings_reader = csv.DictReader(f)
        holdings_map = {row["tradingsymbol"]: float(row["average_price"]) for row in holdings_reader}

    # Prepare closed trade rows
    closed_trades = [["date", "tradingsymbol", "avg_buy_price", "avg_sell_price", "quantity"]]
    for symbol, data in sell_summary.items():
        avg_buy_price = holdings_map.get(symbol, "N/A")  # If not found, show N/A
        closed_trades.append([
            today_str,
            symbol,
            avg_buy_price,
            data["avg_sell_price"],
            data["total_qty"]
        ])

    # Save locally
    with open(output_file, mode="w", newline="") as file:
        writer = csv.writer(file)
        writer.writerows(closed_trades)

    print(f"✅ Saved closed trades to {output_file}")

    # Upload to Google Sheet (overwrite tab)
    sheets.spreadsheets().values().update(
        spreadsheetId=sheet_id,
        range="Closed Trades!A1",
        valueInputOption="RAW",
        body={"values": closed_trades}
    ).execute()

    print("✅ Uploaded to Closed Trades tab in Google Sheet")


# === MAIN ===
def main():
    # Initialize Kite
    kite = KiteConnect(api_key=API_KEY)
    kite.set_access_token(ACCESS_TOKEN)

    # Date and filenames
    today = datetime.now()
    today_str = today.strftime("%d-%m-%Y")
    filename_trades = f"trades_{today.strftime('%d%m%y')}.csv"
    filename_holdings = f"holdings_{today.strftime('%d%m%y')}.csv"

    # Get Data
    trade_data = get_trades(kite, filename_trades, today_str)
    holding_data = get_holdings(kite, filename_holdings, today_str)

    # Upload to Sheets
    sheets, drive = get_services()
    sheet_id = get_or_create_spreadsheet(sheets, drive)
    upload_to_sheet(sheets, sheet_id, trade_data[1:], "Trades", overwrite=False)
    upload_to_sheet(sheets, sheet_id, holding_data[1:], "Holdings", overwrite=True)

    # Get PNL
    generate_closed_trades(today_str, sheets, sheet_id)


if __name__ == "__main__":
    main()
