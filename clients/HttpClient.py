from __future__ import annotations
from abc import ABC, abstractmethod
from typing import List
from clients.DBClient import DBClient
from clients.ClientExceptions import NoExecutableException

import asyncio
import functools
import aiohttp


class Request(ABC):

    # Handle initialisation in the constructor to allow user not to copy it every time
    def __new__(cls, method, base_url, rps, token, **params):
        new = object.__new__(cls)
        new._method = method
        new._base_url = base_url
        new._semaphore = asyncio.Semaphore(rps)
        new._params = params
        new.token = token
        return new

    # Create callback with custom logic: status checking, logging, parsing, saving to database
    @abstractmethod
    async def onResponse(self, response: aiohttp.ClientResponse, client: HttpClient):
        pass

    @abstractmethod
    async def onFailure(self, exception: Exception):
        pass


class HttpClient:
    def __init__(self):
        self._pending_calls = []
        # Check if we have already a running in the backgroundn eventloop, if not create one
        try:
            self._loop, self._using_existing_loop = asyncio.get_running_loop(), True
        except RuntimeError:
            self._loop, self._using_existing_loop = asyncio.get_event_loop(), False

    def connectDB(self, database: DBClient):
        self._loop.create_task(self._connectDB(database))
        return self

    # Add a coroutine to pending requests stack
    def newCall(self, request: Request) -> HttpClient:
        self._pending_calls.append(functools.partial(self._send_request, request))
        return self

    def forEach(self, requests: List[Request]) -> HttpClient:
        self._pending_calls.extend(
            [functools.partial(self._send_request, request) for request in requests]
        )
        return self

    async def _connectDB(self, database):
        self.db = database
        await self.db._start_connection()

    async def _send_request(self, request: Request):
        async with request._semaphore:
            try:
                response = await self._session.request(
                    method=request._method, url=request._base_url
                )
                response.raise_for_status()  # raise ClientResponseError if status is 400+
                # If no exception is raised than we proceed with onResponse callback
                await request.onResponse(response, self)
            except aiohttp.ClientResponseError as exception:
                await request.onFailure(exception)
            finally:
                await asyncio.sleep(1)

    async def _execute_tasks(self):
        async with aiohttp.ClientSession() as self._session:
            await asyncio.gather(*[func() for func in self._pending_calls])

    def execute(self):
        # if a loop exists we just have to submit a new task by calling create task method
        if not self._pending_calls:
            raise NoExecutableException

        if self._using_existing_loop:
            asyncio.create_task(self._execute_tasks())
        # if there is no running loop, we have emplicitly created one so we have to start it as well as
        # pass in coroutine to execute along with it
        else:
            self._loop.run_until_complete(self._execute_tasks())
