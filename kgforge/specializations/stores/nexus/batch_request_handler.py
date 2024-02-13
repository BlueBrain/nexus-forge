from asyncio import AbstractEventLoop
from collections import namedtuple
import json
import asyncio

from typing import Callable, Dict, List, Optional, Tuple, Type, Any, Awaitable
from typing_extensions import Unpack

from aiohttp import ClientSession

from kgforge.core.resource import Resource
from kgforge.core.commons.exceptions import RunException, RetrievalError
from kgforge.specializations.stores.nexus.service import Service, _error_message

BatchResult = namedtuple("BatchResult", ["resource", "response"])
BatchResults = List[BatchResult]


class BatchRequestHandler:

    @staticmethod
    def batch_request(
            service: Service,
            data: List[Any],
            task_creator: Callable[
                [asyncio.Semaphore, ClientSession, AbstractEventLoop, List[Any], Service, Unpack[Any]],
                List[asyncio.Task]
            ],
            **kwargs
    ):

        async def dispatch_action():
            semaphore = asyncio.Semaphore(service.max_connection)
            loop = asyncio.get_event_loop()

            async with ClientSession() as session:
                tasks = task_creator(
                    semaphore, session, loop, data, service, **kwargs
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

        def create_tasks(
                semaphore: asyncio.Semaphore,
                session: ClientSession,
                loop: AbstractEventLoop,
                resources: List[Resource],
                service,
                **kwargs
        ) -> List[asyncio.Task]:

            def init_task(res: Resource):

                batch_result = BatchRequestHandler.request(
                    semaphore=semaphore,
                    session=session,
                    service=service,
                    resource=res,
                    **kwargs
                )
                prepared_request: asyncio.Task = loop.create_task(batch_result)

                if callback:
                    prepared_request.add_done_callback(callback)

                return prepared_request

            return [init_task(res) for res in resources]

        return BatchRequestHandler.batch_request(
            service=service,
            data=resources,
            task_creator=create_tasks,
            prepare_function=prepare_function,
            f_callback=callback,
            **kwargs
        )

    @staticmethod
    async def request(
            semaphore: asyncio.Semaphore,
            session: ClientSession,
            service: Service,
            resource: Optional[Resource],
            prepare_function: Callable[
                [Service, Resource, Dict, Unpack[Any]],
                Tuple[str, str, Resource, Type[RunException], Dict, Optional[Dict], Optional[Dict]]
            ],
            **kwargs
    ) -> BatchResult:

        method, url, resource, exception, headers, params, payload = prepare_function(
            service, resource, **kwargs
        )

        async with semaphore:
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
