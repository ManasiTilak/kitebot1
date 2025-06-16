import csv
from datetime import datetime
import os

def generate_performance_metrics(input_file):
    today = datetime.now().strftime('%d-%m-%Y')
    output_file = f"performance_summary_by_date.csv"  # append daily

    trades = []

    with open(input_file, newline='') as infile:
        reader = csv.DictReader(infile)

        for row in reader:
            try:
                buy = float(row["avg_buy_price"])
                sell = float(row["avg_sell_price"])
                qty = float(row["quantity"])
                date = row["date"].strip()
            except:
                continue

            invested = buy * qty
            sold = sell * qty
            pnl_amount = sold - invested
            pnl_percent = ((sell - buy) / buy) * 100 if buy != 0 else 0

            trades.append({
                "date": date,
                "symbol": row["tradingsymbol"],
                "invested": invested,
                "pnl_amount": pnl_amount,
                "pnl_percent": pnl_percent
            })

    total_invested = sum(t["invested"] for t in trades)
    total_pnl_amount = sum(t["pnl_amount"] for t in trades)
    total_pnl_percent = (total_pnl_amount / total_invested * 100) if total_invested != 0 else 0

    total_trades = len(trades)
    winning = [t for t in trades if t["pnl_amount"] > 0]
    losing = [t for t in trades if t["pnl_amount"] < 0]

    batting_avg = len(winning) / total_trades if total_trades else 0
    loss_rate = len(losing) / total_trades if total_trades else 0

    avg_gain_abs = sum(t["pnl_amount"] for t in winning) / len(winning) if winning else 0
    avg_loss_abs = sum(t["pnl_amount"] for t in losing) / len(losing) if losing else 0

    avg_gain_pct = sum(t["pnl_percent"] for t in winning) / len(winning) if winning else 0
    avg_loss_pct = sum(t["pnl_percent"] for t in losing) / len(losing) if losing else 0

    rr_ratio = abs(avg_gain_abs / avg_loss_abs) if avg_loss_abs != 0 else float('inf')
    expectancy = (batting_avg * avg_gain_abs) - (loss_rate * abs(avg_loss_abs))


    # Prepare row
    row_data = [
        today,
        round(total_invested, 3),
        round(total_pnl_amount, 3),
        round(total_pnl_percent, 2),
        round(batting_avg, 3),
        round(loss_rate, 3),
        round(avg_gain_abs, 3),
        round(abs(avg_loss_abs), 3),
        round(avg_gain_pct, 3),
        round(abs(avg_loss_pct), 3),
        round(rr_ratio, 3),
        round(expectancy, 3)
    ]

    # Write (append) to CSV
    file_exists = os.path.exists(output_file)
    with open(output_file, mode="a", newline="") as outfile:
        writer = csv.writer(outfile)
        if not file_exists:
            writer.writerow([
                "date", "total_amount_invested", "total_pnl_amount", "total_pnl_percent",
                "batting_avg", "loss_rate", "avg_gain_abs", "avg_loss_abs",
                "avg_gain_pct", "avg_loss_pct", "risk_reward_ratio", "expectancy"
            ])
        writer.writerow(row_data)

    print(f"Appended performance row to {output_file}")


# Run
if __name__ == "__main__":
    input_csv = "closed_trades_130625.csv"  # Replace with your file
    if os.path.exists(input_csv):
        generate_performance_metrics(input_csv)
    else:
        print(f"File not found: {input_csv}")
