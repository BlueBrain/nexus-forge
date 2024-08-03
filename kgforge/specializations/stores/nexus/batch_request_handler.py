from asyncio import AbstractEventLoop
from collections import namedtuple
import json
import asyncio

from typing import Callable, Dict, List, Optional, Tuple, Type, Any

from kgforge.core.commons.constants import DEFAULT_REQUEST_TIMEOUT

import aiohttp
from typing_extensions import Unpack

from aiohttp import ClientSession, ClientTimeout

from kgforge.core.resource import Resource
from kgforge.core.commons.exceptions import RunException
from kgforge.specializations.stores.nexus.service import Service, _error_message

BatchResult = namedtuple("BatchResult", ["resource", "response"])
BatchResults = List[BatchResult]

BATCH_REQUEST_TIMEOUT_PER_REQUEST = DEFAULT_REQUEST_TIMEOUT


class BatchRequestHandler:

    @staticmethod
    def batch_request(
            service: Service,
            data: List[Any],
            task_creator: Callable[
                [asyncio.Semaphore, AbstractEventLoop, List[Any], Service, Unpack[Any]],
                List[asyncio.Task]
            ],
            **kwargs
    ):

        async def dispatch_action():
            semaphore = asyncio.Semaphore(service.max_connection)
            loop = asyncio.get_event_loop()

            tasks = task_creator(
                semaphore, loop, data, service, **kwargs
            )
            return await asyncio.gather(*tasks)

        return asyncio.run(dispatch_action())

    @staticmethod
    def batch_request_on_resources(
            service: Service,
            resources: List[Resource],
            prepare_function: Callable[
                ['Service', Resource, Dict, Unpack[Any]],
                Tuple[str, str, Resource, Type[RunException], Dict, Optional[Dict], Optional[Dict]]
            ],
            callback: Callable,
            **kwargs
    ) -> BatchResults:

        return BatchRequestHandler.batch_request(
            service=service,
            data=resources,
            task_creator=BatchRequestHandler.create_tasks_for_resources,
            prepare_function=prepare_function,
            callback=callback,
            **kwargs
        )

    @staticmethod
    def create_tasks_for_resources(
            semaphore: asyncio.Semaphore,
            session: ClientSession,
            loop: AbstractEventLoop,
            resources: List[Resource],
            service,
            **kwargs
    ) -> List[asyncio.Task]:

        prepare_function = kwargs["prepare_function"]
        callback = kwargs["callback"]

        async def request(resource: Optional[Resource]) -> BatchResult:

            method, url, resource, exception, headers, params, payload = prepare_function(
                service, resource, **kwargs
            )

            async with semaphore:

                async with ClientSession(connector=aiohttp.TCPConnector(force_close=True)) as session:

                    async with session.request(
                            method=method,
                            url=url,
                            headers=headers,
                            data=json.dumps(payload, ensure_ascii=True),
                            params=params
                    ) as response:
                        content = await response.json()
                        if response.status < 400:
                            return BatchResult(resource, content)

                        error = exception(_error_message(content))
                        return BatchResult(resource, error)

        tasks = []

        for res in resources:

            prepared_request: asyncio.Task = loop.create_task(request(res))

            if callback:
                prepared_request.add_done_callback(callback)

            tasks.append(prepared_request)

        return tasks
