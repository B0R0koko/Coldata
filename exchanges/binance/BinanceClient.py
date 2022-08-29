from clients.HttpClient import HttpClient, Request


class BinanceClient(HttpClient):
    def __init__(self):
        super().__init__()
