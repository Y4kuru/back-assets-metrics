from dataclasses import asdict
import json
from app.mocks.mock_response import OVERVIEW, GLOBAL_QUOTE, TIME_SERIES_MONTHLY_ADJUSTED
import os
from app.domain.stocks_domain import buil_companies_data_from_dataframe, get_companies_data_from_file, is_data_recent, safe_number
from app.models.companies import Company
import pandas as pd
import os
from datetime import date

GOOGLE_SHEET_CSV_PEA_URL = os.getenv("GOOGLE_SHEET_CSV_PEA_URL", "")
GOOGLE_SHEET_CSV_HISTORY_PEA_URL = os.getenv("GOOGLE_SHEET_CSV_HISTORY_PEA_URL", "")
GOOGLE_SHEET_CSV_CTO_URL = os.getenv("GOOGLE_SHEET_CSV_CTO_URL", "")
GOOGLE_SHEET_CSV_HISTORY_CTO_URL = os.getenv("GOOGLE_SHEET_CSV_HISTORY_CTO_URL", "")

def get_company_data(ticker: str):
    all_companies_data = get_companies_data()
    for company in all_companies_data['pea']:
        if company.ticker == ticker:
            return asdict(company)
    for company in all_companies_data['cto']:
        if company.ticker == ticker:
            return asdict(company)
    return {"error": "Ticker not found"}, 404


# def safe_fetch(url: str, ticker: str) -> dict:
#     try:
#         r = requests.get(url, timeout=10)
#         if r.status_code != 200:
#             print(f"[{ticker}] Request failed: {r.status_code}")
#             return {}
#         return r.json()
#     except requests.exceptions.RequestException as e:
#         print(f"[{ticker}] Exception during request: {e}")
#         return {}
#     except Exception as e:
#         print(f"[{ticker}] Unexpected error: {e}")
#         return {}


# def fetch_companies_data(list_tickers: list[str]) -> list[Company]:
#     companies_data = []

#     for ticker in list_tickers:
#         print(f"Fetching {ticker}...")
#         # local mock data
#         # company = build_company_data(OVERVIEW, GLOBAL_QUOTE, TIME_SERIES_MONTHLY_ADJUSTED['Monthly Adjusted Time Series'])

#         overview = safe_fetch(f'https://www.alphavantage.co/query?function=OVERVIEW&symbol={ticker}&apikey={API_KEY}', ticker)
#         time.sleep(12)

#         global_quote = safe_fetch(f'https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={ticker}&apikey={API_KEY}', ticker)
#         time.sleep(12)

#         time_series_data = safe_fetch(f'https://www.alphavantage.co/query?function=TIME_SERIES_MONTHLY_ADJUSTED&symbol={ticker}&apikey={API_KEY}', ticker)
#         time.sleep(12)

#         try:
#             monthly_series = time_series_data.get('Monthly Adjusted Time Series', {})
#             if not overview or not global_quote or not monthly_series:
#                 print(f"[{ticker}] Incomplete data — skipping.")
#                 continue

#             company = build_company_data(overview, global_quote, monthly_series)
#             if company:
#                 companies_data.append(company)

#         except Exception as e:
#             print(f"[{ticker}] Error building company: {e}")

#     return companies_data


def load_companies_data():
    is_pea_loaded = is_data_recent('PEA', 0)
    is_cto_loaded = is_data_recent('CTO', 0)
    if is_pea_loaded and is_cto_loaded:
        print("Data already loaded for PEA and CTO.")
        companies_data_pea = get_companies_data_from_file('PEA')
        companies_data_cto = get_companies_data_from_file('CTO')
        return get_companies_data(), 200
    companies_data_pea = download_and_parse_sheet(GOOGLE_SHEET_CSV_PEA_URL, GOOGLE_SHEET_CSV_HISTORY_PEA_URL)
    companies_data_cto = download_and_parse_sheet(GOOGLE_SHEET_CSV_CTO_URL, GOOGLE_SHEET_CSV_HISTORY_CTO_URL)
    save_to_json(companies_data_pea, watchlist_name="PEA")
    save_to_json(companies_data_cto, watchlist_name="CTO")
    
    # if is_pea_loaded and is_cto_loaded:
    #     print("Data already saved for PEA and CTO.")
    #     return {}, 200
    # if not is_pea_loaded:
    #     print("PEA data not saved, fetching...")
    #     company_pea = WATCHLIST_PEA
    #     companies_data_pea = fetch_companies_data(company_pea)
    #     save_companies_data(companies_data_pea, 'data/PEA')
    # if not is_cto_loaded:
    #     print("CTO data not saved, fetching...")
    #     company_cto = WATCHLIST_CTO
    #     companies_data_cto = fetch_companies_data(company_cto)
    #     save_companies_data(companies_data_cto, 'data/CTO')
    return { 'pea': companies_data_pea, 'cto': companies_data_cto}, 200


def get_companies_data() -> list[Company]:
    return { 
        'pea': get_companies_data_from_file('PEA'),
        'cto': get_companies_data_from_file('CTO')
    }
    
def get_companies_data_pea() -> list[Company]:
    print("get_companies_data_pea")
    return get_companies_data_from_file('PEA')

def get_companies_data_cto() -> list[Company]:
    print("get_companies_data_cto")
    return get_companies_data_from_file('CTO')

def download_and_parse_sheet(url_data: str, url_history: str) -> list[dict]:
    df = pd.read_csv(url_data, on_bad_lines='skip')
    df.columns = df.columns.str.strip().str.replace('\ufeff', '')  # clean headers
    df_history = pd.read_csv(url_history, on_bad_lines='skip', header=0)
    companies = buil_companies_data_from_dataframe(df, df_history)
    return companies


def save_to_json(companies, watchlist_name="PEA"):
    today = date.today().isoformat()
    folder = f"data/{watchlist_name}"
    os.makedirs(folder, exist_ok=True)
    filename = f"{today}-{watchlist_name}.json"
    path = os.path.join(folder, filename)

    # ✅ Save new data
    with open(path, "w", encoding="utf-8") as f:
        json.dump(companies, f, indent=2, ensure_ascii=False)
    print(f"✅ Data saved to {path}")

    # 🧹 Delete old files
    for fname in os.listdir(folder):
        if fname.endswith(".json") and fname != filename:
            try:
                os.remove(os.path.join(folder, fname))
                print(f"🗑️ Deleted old file: {fname}")
            except Exception as e:
                print(f"⚠️ Failed to delete {fname}: {e}")