from datetime import date, datetime, timedelta
import json
import math
import os
from typing import Union
from app.models.companies import Company
from dataclasses import asdict

def build_company_data(company_info: any, global_quote: any, time_series: any) -> Union[Company, None]:
    company = None
    try:
        price = float(global_quote['Global Quote']['05. price'])
        high_price = float(company_info['52WeekHigh'])
        drop_from_high = f"{((price - high_price) / high_price) * 100:.2f}%"
        price_history_10y = get_last_10_years_price_history(time_series)
        company = Company(
            ticker=company_info['Symbol'],
            name=company_info['Name'],
            market_cap=company_info['MarketCapitalization'],
            currency=company_info['Currency'],
            price=global_quote['Global Quote']['05. price'],
            high_price=company_info['52WeekHigh'],
            drop_from_high=drop_from_high,
            pe=str(company_info['PERatio']),
            daily_change=global_quote['Global Quote']['10. change percent'],
            eps=str(company_info['EPS']),
            sector=company_info['Sector'].lower(),
            moat='-',
            price_history=price_history_10y
        )
    except KeyError as e:
        print(f"KeyError: {e} - Missing data in company_info or global_quote")
        return None
    except Exception as e:
        print(f"An error occurred while building company data: {e}")
        return None
    return company

def get_last_10_years_price_history(time_series: dict) -> list[float]:
    ten_years_ago = datetime.today().replace(day=1) - timedelta(days=365 * 10)
    return [
        float(data["5. adjusted close"])
        for date_str, data in sorted(time_series.items())
        if datetime.strptime(date_str, "%Y-%m-%d") >= ten_years_ago
    ]


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

def is_data_recent(companies_type: str, max_age_days: int = 4) -> bool:
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