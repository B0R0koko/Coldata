from clients.HttpClient import HttpClient, Request
from clients.DBClient import DBClient


class MyRequest(Request):

    data = {"data": []}

    async def onResponse(self, response, client):
        print(f"Got response {self.token}")
        await client.db.execute("INSERT INTO cars VALUES ($1)", [9])
        self.data["data"].append(await response.json())

    async def onFailure(self, exception):
        print("Exception")


request_1 = MyRequest(
    "GET",
    "https://api.binance.com/api/v3/klines?symbol=BTCUSDT&interval=1h",
    1,
    "task1",
)

request_2 = MyRequest(
    "GET",
    "https://api.binance.com/api/v3/klines?symbol=BTCUSDT&interval=2h",
    1,
    "task2",
)

db = DBClient("loalhost", "----", "-----", "5432", "postgres")

client = HttpClient()

client.connectDB(db).forEach([request_1, request_2] * 10).execute()
