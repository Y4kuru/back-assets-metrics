from datetime import date, datetime, timedelta
import json
import math
import os
import re
from typing import List, Union

from pandas import DataFrame, Series
from app.models.companies import Company
from dataclasses import asdict

SECTOR_PE_BASELINES = {
    'technologie': 20,
    'santé': 18,
    'santé/healthcare': 18,
    'énergie': 12,
    'industrie': 15,
    'luxe': 25,
    'finance': 12,
    'services': 15,
    'consommation': 18,
    'media': 16
}
DEFAULT_PE_BASELINE = 15

# def build_company_data(company_info: dict, global_quote: dict, time_series: dict) -> Union[Company, None]:
#     company = None
#     try:
#         price = float(global_quote['Global Quote']['05. price'])
#         high_price = float(company_info['52WeekHigh'])
#         drop_from_high = f"{((price - high_price) / high_price) * 100:.2f}%"
#         price_history_10y = get_last_10_years_price_history(time_series)
#         discount, fair_value =  calculate_fair_discount_and_fair_value(company_info, price)      
#         attractiveness_score = calculate_attractiveness_score(company_info, price, high_price)
#         company = Company(
#             ticker=company_info['Symbol'],
#             name=company_info['Name'],
#             market_cap=company_info['MarketCapitalization'],
#             currency=company_info['Currency'],
#             price=global_quote['Global Quote']['05. price'],
#             high_price=company_info['52WeekHigh'],
#             drop_from_high=drop_from_high,
#             pe=str(company_info['PERatio']),
#             daily_change=global_quote['Global Quote']['10. change percent'],
#             eps=str(company_info['EPS']),
#             sector=company_info['Sector'].lower(),
#             fair_value_gap=safe_number(discount),
#             fair_value=safe_number(fair_value),
#             attractiveness_score=attractiveness_score,
#             moat='-',
#             price_history=price_history_10y,
#             price_dates=[]
#         )
#     except KeyError as e:
#         print(f"KeyError: {e} - Missing data in company_info or global_quote")
#         return None
#     except Exception as e:
#         print(f"An error occurred while building company data: {e}")
#         return None
#     return company

def get_last_10_years_price_history(time_series: dict) -> list[float]:
    ten_years_ago = datetime.today().replace(day=1) - timedelta(days=365 * 10)
    return [
        float(data["5. adjusted close"])
        for date_str, data in sorted(time_series.items())
        if datetime.strptime(date_str, "%Y-%m-%d") >= ten_years_ago
    ]

def parse_float(value: any) -> float:
    """Cleans and converts a string to float, returns 0.0 if invalid."""
    try:
        if isinstance(value, (int, float)):
            return float(value)
        value = re.sub(r'[^\d\-,\.]', '', str(value))  # keep digits, dot, comma, minus
        value = value.replace(',', '.')  # convert comma decimal to dot
        return float(value)
    except:
        return 0.0

def calculate_fair_discount_and_fair_value(row: Series) -> tuple[float, float]:
    try:
        sector = str(row.get("Secteur", "")).lower()
        baseline_pe = SECTOR_PE_BASELINES.get(sector, DEFAULT_PE_BASELINE)

        eps = parse_float(row.get("EPS", 0))
        price = parse_float(row.get("Price", 0))

        if eps <= 0:
            return 0.0, 0.0

        fair_value = eps * baseline_pe
        discount = ((fair_value - price) / fair_value) * 100
        return round(discount, 2), round(fair_value, 2)

    except Exception as e:
        print(f"Error calculating fair discount: {e}")
        return 0.0, 0.0


def calculate_attractiveness_score(row: Series) -> int:
    try:
        pe = parse_float(row.get("PE", 0))
        eps = parse_float(row.get("EPS", 0))
        price = parse_float(row.get("Price", 0))
        high = parse_float(row.get("Plus haut prix", 0))

        drop = (price - high) / high if high else 0

        sector = str(row.get("Secteur", "")).lower()
        baseline_pe = SECTOR_PE_BASELINES.get(sector, DEFAULT_PE_BASELINE)

        pe_score = max(0, min(1, (baseline_pe * 2 - pe) / baseline_pe))
        eps_score = max(0, min(1, (eps + 5) / 25))
        drop_score = max(0, min(1, abs(drop) / 0.5))

        attractiveness = int((pe_score * 0.3 + eps_score * 0.3 + drop_score * 0.4) * 100)
        return attractiveness
    except Exception as e:
        print(f"Error calculating attractiveness score: {e}")
        return 0


def save_companies_data(companies: list[Company], save_path: str='data') -> None:
    postfix = save_path.replace('data/', '')
    os.makedirs(save_path, exist_ok=True)
    today = date.today().isoformat()
    filename = f"{today}-{postfix}.json"
    filepath = os.path.join(save_path, filename)
    json_ready_companies = [asdict(company) for company in companies]
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(json_ready_companies, f, ensure_ascii=False, indent=2)
    print(f"✅ Saved company data to {filepath}")

def is_companies_data_recent(companies_type: str, max_age_days: int = 4) -> bool:
    folder = 'data/PEA' if companies_type == 'PEA' else 'data/CTO'
    today = date.today()

    try:
        files = [f for f in os.listdir(folder) if f.endswith(f"-{companies_type}.json")]
        dates = []
        for file in files:
            try:
                date_str = file.split(f"-{companies_type}.json")[0]
                file_date = datetime.strptime(date_str, "%Y-%m-%d").date()
                dates.append(file_date)
            except ValueError:
                continue 
        if not dates:
            return False 
        most_recent = max(dates)
        age = (today - most_recent).days
        return age <= max_age_days

    except Exception as e:
        print(f"[{companies_type}] Erreur lors de la vérification de la date des fichiers : {e}")
        return False

def buil_companies_data_from_dataframe(df: DataFrame, df_history: DataFrame) -> List[Company]:
    companies = []

    for i, row in df.iterrows():
        ticker = str(row["Ticker"]).strip()
        discount, fair_value = calculate_fair_discount_and_fair_value(row)      
        attractiveness_score = calculate_attractiveness_score(row)
        company = {
            "ticker": ticker,
            "name": row["Nom"],
            "market_cap": row["Market Cap"],
            "currency": row["Devise"],
            "price": row["Price"],
            "high_price": row["Plus haut prix"],
            "drop_from_high": row["Plus haut"],
            "pe": safe_number(row["PE"]),
            "daily_change": row["cours J %"],
            "eps": safe_number(row["EPS"]),
            "sector": row["Secteur"],
            "fair_value_gap": safe_number(discount),
            "fair_value": safe_number(fair_value),
            "attractiveness_score": attractiveness_score,
            "moat": row.get("Type de Moat principal", ""),
            "price_history": [],
            "price_dates": []
        }

        # Get columns: assume (Date | Close) repeating
        date_col_idx = i * 2
        price_col_idx = i * 2 + 1

        if price_col_idx < df_history.shape[1]:
            raw_dates = df_history.iloc[:, date_col_idx].dropna().astype(str).tolist()
            raw_prices = df_history.iloc[:, price_col_idx].dropna().astype(str).tolist()

            price_history = []
            price_dates = []

            for date_str, price_str in zip(raw_dates, raw_prices):
                try:
                    price = float(price_str.replace(",", ".").replace("€", "").strip())
                    date_only = date_str.split(" ")[0]
                    price_history.append(price)
                    price_dates.append(date_only)
                except ValueError:
                    continue

            company["price_history"] = price_history
            company["price_dates"] = price_dates

        companies.append(company)
    return companies

def get_companies_data_from_file(companies_type: str) -> list[Company]:
    today = date.today().isoformat()
    filename = f"{today}-{companies_type}.json"
    folder = 'data/PEA' if companies_type == 'PEA' else 'data/CTO'  
    filepath = os.path.join(folder, filename)
    if not os.path.exists(filepath):
        print(f"File {filepath} does not exist.")
        return []
    with open(filepath, 'r', encoding='utf-8') as f:
        companies_data = json.load(f)
    return [Company(**data) for data in companies_data]

def safe_number(val):
    try:
        if isinstance(val, float) and math.isnan(val):
            return None
        return val
    except:
        return None