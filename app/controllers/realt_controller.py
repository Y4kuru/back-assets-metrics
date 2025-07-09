from io import StringIO
import os
import requests
import json
import pandas as pd
from datetime import date, datetime
from flask import jsonify

RENT_DATA_FOLDER = "data/realt/rent"
RENT_URL = os.getenv("GOOGLE_SHEET_CSV_REALT_RENT_URL", "")

def is_realt_rent_data_recent(max_age_days: int = 4) -> bool:
    today = date.today()
    try:
        files = [f for f in os.listdir(RENT_DATA_FOLDER) if f.endswith("rent.json")]
        dates = []
        for file in files:
            try:
                date_str = file.replace("-rent.json", "")
                file_date = datetime.strptime(date_str, "%Y-%m-%d").date()
                dates.append(file_date)
            except ValueError:
                continue
        if not dates:
            return False
        most_recent = max(dates)
        return (today - most_recent).days <= max_age_days
    except Exception as e:
        print(f"[Rent Check] Error: {e}")
        return False

def load_and_get_realt_rent_data():
    today_str = date.today().isoformat()
    filepath = os.path.join(RENT_DATA_FOLDER, f"{today_str}-rent.json")

    try:
        # Load if data not recent
        if not is_realt_rent_data_recent():
            print("Fetching new rent data...")

            full_url = f"{RENT_URL}"
            df = pd.read_csv(full_url, on_bad_lines='skip')

            df = df.dropna(subset=["Date", "Rent"])
            df["Date"] = pd.to_datetime(df["Date"], format="%d/%m/%Y")
            df["Rent"] = (
                df["Rent"]
                .astype(str)
                .str.replace("$", "")
                .str.replace(",", ".")
                .astype(float)
            )

            rent_data = [
                {"date": d.strftime("%Y-%m-%d"), "rent": r}
                for d, r in zip(df["Date"], df["Rent"])
            ]

            os.makedirs(RENT_DATA_FOLDER, exist_ok=True)
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(rent_data, f, indent=2, ensure_ascii=False)

            print(f"✅ Rent data saved to {filepath}")

        else:
            print("✅ Using cached rent data")

        # Load latest rent file
        files = [f for f in os.listdir(RENT_DATA_FOLDER) if f.endswith("rent.json")]
        latest_file = max(files, key=lambda f: f.split("-")[0])
        filepath = os.path.join(RENT_DATA_FOLDER, latest_file)

        with open(filepath, "r", encoding="utf-8") as f:
            rent_data = json.load(f)

        # Split into labels and data
        response = {
            "dates": [item["date"] for item in rent_data],
            "rents": [item["rent"] for item in rent_data],
        }

        return jsonify(response), 200

    except Exception as e:
        print(f"[Rent Load/Get] Error: {e}")
        return jsonify({"error": "Failed to process rent data"}), 500


# def is_realt_rent_data_recent(max_age_days: int = 4) -> bool:
#     today = date.today()

#     try:
#         files = [f for f in os.listdir(RENT_DATA_FOLDER) if f.endswith("rent.json")]
#         dates = []
#         for file in files:
#             try:
#                 date_str = file.replace("-rent.json", "")
#                 file_date = datetime.strptime(date_str, "%Y-%m-%d").date()
#                 dates.append(file_date)
#             except ValueError:
#                 continue
#         if not dates:
#             return False
#         most_recent = max(dates)
#         return (today - most_recent).days <= max_age_days
#     except Exception as e:
#         print(f"[Rent Check] Error: {e}")
#         return False

# def load_realt_rent_data():
#     if is_realt_rent_data_recent():
#         print("✅ Rent data already saved.")
#         return jsonify({"status": "already_fresh"}), 200

#     try:
#         response = requests.get(RENT_URL + "219855821" + END_OF_URL)
#         response.raise_for_status()

#         df = pd.read_csv(pd.compat.StringIO(response.text))
#         df = df.dropna(subset=["Date", "Rent"])
#         df["Date"] = pd.to_datetime(df["Date"], format="%d/%m/%Y")
#         df["Rent"] = df["Rent"].astype(str).str.replace("$", "").str.replace(",", ".").astype(float)

#         rent_data = [
#             {"date": d.strftime("%Y-%m-%d"), "rent": r}
#             for d, r in zip(df["Date"], df["Rent"])
#         ]

#         today_str = date.today().isoformat()
#         os.makedirs(RENT_DATA_FOLDER, exist_ok=True)
#         filepath = os.path.join(RENT_DATA_FOLDER, f"{today_str}-rent.json")

#         with open(filepath, "w", encoding="utf-8") as f:
#             json.dump(rent_data, f, indent=2, ensure_ascii=False)

#         print(f"✅ Rent data saved to {filepath}")
#         return jsonify({"status": "saved"}), 200

#     except Exception as e:
#         print(f"[Rent Load] Error: {e}")
#         return jsonify({"error": "Failed to load rent data"}), 500

# def get_realt_rent_data():
#     try:
#         files = [f for f in os.listdir(RENT_DATA_FOLDER) if f.endswith("rent.json")]
#         if not files:
#             return jsonify({"error": "No rent data available"}), 404

#         latest_file = max(files, key=lambda f: f.split("-")[0])
#         filepath = os.path.join(RENT_DATA_FOLDER, latest_file)

#         with open(filepath, "r", encoding="utf-8") as f:
#             rent_data = json.load(f)

#         return jsonify(rent_data), 200

#     except Exception as e:
#         print(f"[Rent Get] Error: {e}")
#         return jsonify({"error": "Failed to load rent data"}), 500
