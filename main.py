from datetime import datetime, timedelta
import aiohttp
import asyncio
import json
import sys
import pprintpp



URL = "https://api.privatbank.ua/p24api/exchange_rates?json&date="
HEADERS = {'user-agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Mobile Safari/537.36'}
TIMEOUT = aiohttp.ClientTimeout(total=50)



def created_data(how_many_days: int):

    current_date = datetime.now()
    for n in range(how_many_days):
        past = timedelta(days=n)
        past_date = current_date - past  
        today = past_date.strftime("%d.%m.%Y")
        yield today


async def get_data(date: str):
    data = {}
    async with aiohttp.ClientSession(headers=HEADERS, timeout=TIMEOUT)as session:
        try:
            async with session.get(f'{URL}{date}') as response:
                if response.status == 200:
                    body = await response.text()
                    data.update(json.loads(body))
                else:
                    print(f"Error status: {response.status} for {URL}")
        except aiohttp.ClientConnectorError as err:
            print(f'Connection error: {URL}', str(err))
    
    return data

async def corrector_data(data: dict, date: str):
    corect_data = {}
    usd = {}
    eur = {}
    exchange_list = data['exchangeRate']
    
    for i in exchange_list:
        if i['currency'] == 'USD':
            usd['USD'] = {'sale': i['saleRateNB'], 'purchase': i['purchaseRateNB']}
        if i['currency'] == 'EUR':
            eur['EUR'] = {'sale': i['saleRateNB'], 'purchase': i['purchaseRateNB']}
    
    corect_data[date] = usd
    corect_data[date].update(eur)
    return corect_data
    

async def main(how_many_days=2):

    if how_many_days >= 10:
        return "Error: In this utility, you can find out the exchange rate for no more than the last 10 days"
    exchenge_list = []
    for date in created_data(how_many_days):
        data = await get_data(date)
        correct_data = await corrector_data(data, date)
        exchenge_list.append(correct_data)
    pprintpp.pprint(exchenge_list)



if __name__ == "__main__":
    asyncio.run(main(int(sys.argv[1])))