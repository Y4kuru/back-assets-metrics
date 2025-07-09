from . import api
from app.controllers.stocks_controller import get_company_data, load_companies_data

@api.route('/load_companies', methods=['POST'])
def load_companies():
    return load_companies_data()

@api.route('/company/<ticker>', methods=['GET'])
def get_company(ticker):
    return get_company_data(ticker)

# @api.route('/stock/<ticker>', methods=['GET'])
# def get_stock(ticker):
#     return get_stock_data(ticker)
