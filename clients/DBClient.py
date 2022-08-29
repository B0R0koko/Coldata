from typing import Any, List
import asyncpg


class DBClient:
    def __init__(self, host, user, password, port, database):
        self._host = host
        self._user = user
        self._password = password
        self._port = port
        self._database = database

    async def _start_connection(self):
        self._conn = await asyncpg.create_pool(
            host=self._host,
            user=self._user,
            password=self._password,
            port=self._port,
            database=self._database,
        )

    async def execute(self, query: str, data: List[Any]):
        await self._conn.execute(query, *data)

    async def execute_many(self, query: str, data: List[List[Any]]):
        await self._conn.executemany(query, data)
