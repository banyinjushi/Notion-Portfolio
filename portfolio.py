import requests
from forex_python.converter import CurrencyRates

secret = "secret_xx" # your notion secret token
base_db_url = "https://api.notion.com/v1/databases/"
base_pg_url = "https://api.notion.com/v1/pages/"
base_crypto_url = "https://api.coinlore.net/api/tickers/?start=0&limit=100"
base_stock_url = "http://hq.sinajs.cn/list="
stock_headers = {
            'Referer': 'http://finance.sina.com.cn'
        }
wallet_db_id = "xx" #  yourdatabase id
data = {}
header = {"Authorization":secret, "Notion-Version":"2021-05-13", "Content-Type": "application/json"}
response = requests.post(base_db_url + wallet_db_id + "/query", headers=header, data=data)

def get_exchange_rate(base_currency, target_currency):
    api_url = f"https://api.exchangerate-api.com/v4/latest/{base_currency}"
    response = requests.get(api_url)
    if response.status_code == 200:
        data = response.json()
        rate = data['rates'].get(target_currency)
        if rate:
            return rate
        else:
            return 0
    else:
        return 0

for page in response.json()["results"]:
    page_id = page["id"]
    props = page['properties']

    try:
        asset_type = props['Market']['select']['name']
        asset_code = props['Code']['rich_text'][0]['plain_text']
        print(f'asset_code:{asset_code}')
    except Exception as e:
        # print(f'get assert code failed: {page}')
        continue

    if asset_type == "美股" or asset_type == "A股"  or asset_type == "港股":
        url = f"{base_stock_url}{asset_code}"
        response = requests.get(url, headers=stock_headers)
        if response.status_code != 200:
            print("Error: Unable to fetch data")
            continue
        data = response.text
        details = data.split(',')
        print(details)
        if asset_type == "美股":
            price = details[1]
            price_cn = float(price) * get_exchange_rate('USD', 'CNY')
        elif asset_type == "A股":
            price = details[3]
            price_cn = price
        elif asset_type == "港股":
            price = details[6]
            price_cn = float(price) * get_exchange_rate('HKD', 'CNY')
        print(f'asset_code:{asset_code}, price:{price}')

        data_price = '{"properties": {"Price": { "number":' + str(round(float(price),2)) + '},\
                                                "Price_CN": { "number":' + str(round(float(price_cn),2)) + '}}}'
                                        
        send_price = requests.patch(base_pg_url + page_id, headers=header, data=data_price)

    if asset_type == "数字货币":
        request_by_code = requests.get(base_crypto_url).json()['data']
        coin = next((item for item in request_by_code if item["symbol"] == asset_code), None)
        if(request_by_code != []):
            price = coin['price_usd']
            price_cn = float(price) * get_exchange_rate('USD', 'CNY')
            data_price = '{"properties": {"Price": { "number":' + str(round(float(price),2)) + '},\
                                                "Price_CN": { "number":' + str(round(float(price_cn),2)) + '}}}'
            send_price = requests.patch(base_pg_url + page_id, headers=header, data=data_price)
