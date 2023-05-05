import aiohttp
import asyncio
import logging
import websockets
import names
import json
from datetime import datetime, timedelta
from websockets import WebSocketServerProtocol
from websockets.exceptions import ConnectionClosedOK




URL = "https://api.privatbank.ua/p24api/exchange_rates?json&date="
HEADERS = {'user-agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Mobile Safari/537.36'}
TIMEOUT = aiohttp.ClientTimeout(total=50)



logging.basicConfig(level=logging.INFO)

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

async def corrector_data(data: dict, date: str, currency: str):
    corect_data = {}
    curr = {}
    exchange_list = data['exchangeRate']   
    for i in exchange_list:
        if i['currency'] == currency:
            curr[currency] = {'sale': i['saleRateNB'], 'purchase': i['purchaseRateNB']}
    corect_data[date] = curr
    return corect_data


async def main_exchange(currency, how_many_days=1):

    if how_many_days >= 10:
        return "Error: In this utility, you can find out the exchange rate for no more than the last 10 days"
    exchenge_list = []
    for date in created_data(how_many_days):
        data = await get_data(date)
        correct_data = await corrector_data(data, date, currency)
        exchenge_list.append(correct_data)
    a = str(exchenge_list).replace("{", "")
    b = a.replace("}", "")
    return b


class Server:
    clients = set()

    async def register(self, ws: WebSocketServerProtocol):
        ws.name = names.get_full_name()
        self.clients.add(ws)
        logging.info(f'{ws.remote_address} connects')

    async def unregister(self, ws: WebSocketServerProtocol):
        self.clients.remove(ws)
        logging.info(f'{ws.remote_address} disconnects')

    async def send_to_clients(self, message: str):
        if self.clients:
            [await client.send(message) for client in self.clients]

    async def ws_handler(self, ws: WebSocketServerProtocol):
        await self.register(ws)
        try:
            await self.distrubute(ws)
        except ConnectionClosedOK:
            pass
        finally:
            await self.unregister(ws)

    async def distrubute(self, ws: WebSocketServerProtocol):
        async for message in ws:
            if message.startswith("exchange"):
                sm = message.split(" ")
                if sm == ["exchange"]:
                    r = await main_exchange("USD", 1)
                    await self.send_to_clients(r)
                    continue
                if len(sm) == 2:
                    r = await main_exchange(sm[1], 1)
                else:
                    r = await main_exchange(sm[1], int(sm[2]))
                await self.send_to_clients(r)
            else:
                await self.send_to_clients(f"{ws.name}: {message}")


async def main():
    server = Server()
    async with websockets.serve(server.ws_handler, 'localhost', 8080):
        await asyncio.Future()  # run forever

if __name__ == '__main__':
    asyncio.run(main())