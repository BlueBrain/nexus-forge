from asyncio import AbstractEventLoop
from collections import namedtuple
import json
import asyncio

from typing import Callable, Dict, List, Optional, Tuple, Type, Any, Coroutine, Union

from kgforge.core.commons.actions import Action
from kgforge.core.commons.constants import DEFAULT_REQUEST_TIMEOUT

from typing_extensions import Unpack

from aiohttp import ClientSession, ClientTimeout

from kgforge.core.resource import Resource
from kgforge.core.commons.exceptions import RunException
from kgforge.specializations.stores.nexus.service import Service, _error_message

BatchResult = namedtuple("BatchResult", ["resource", "response"])
BatchResults = List[BatchResult]

BATCH_REQUEST_TIMEOUT_PER_REQUEST = DEFAULT_REQUEST_TIMEOUT


class BatchRequestHandler:
    BATCH_SIZE = 80

    @staticmethod
    def batch(iterable, n=BATCH_SIZE):

        length_v = len(iterable)
        for ndx in range(0, length_v, n):
            yield iterable[ndx:min(ndx + n, length_v)]

    @staticmethod
    def batch_request(
            service: Service,
            data: List[Any],
            task_creator: Callable[
                [asyncio.Semaphore, AbstractEventLoop, List[Any], Service, Unpack[Any]],
                Coroutine[Any, Any, Tuple[List[asyncio.Task], List[ClientSession]]]
            ],
            **kwargs
    ):

        loop = asyncio.get_event_loop()

        async def dispatch_action():
            semaphore = asyncio.Semaphore(service.max_connection)

            tasks, sessions = await task_creator(
                semaphore, loop, data, service, **kwargs
            )

            return await asyncio.gather(*tasks), sessions

        async def close_sessions(sesss):
            for sess in sesss:
                await sess.close()

        res, sessions = asyncio.run(dispatch_action())
        closing_task = loop.create_task(close_sessions(sessions))
        asyncio.run(closing_task)
        return res

    @staticmethod
    def batch_request_on_resources(
            service: Service,
            resources: List[Resource],
            prepare_function: Callable[
                ['Service', Resource, Dict, Unpack[Any]],
                Tuple[str, str, Resource, Type[RunException], Dict, Optional[Dict], Optional[Dict]]
            ],
            callback: Optional[Callable] = None,
            **kwargs
    ) -> BatchResults:

        async def create_tasks_for_resources(
                semaphore: asyncio.Semaphore,
                loop: AbstractEventLoop,
                resources: List[Resource],
                service,
                **kwargs
        ) -> Tuple[List[asyncio.Task], List[ClientSession]]:

            prepare_function = kwargs["prepare_function"]
            callback = kwargs["callback"]

            async def request(resource: Optional[Resource], client_session: ClientSession) -> BatchResult:

                method, url, resource, exception, headers, params, payload = prepare_function(
                    service, resource, **kwargs
                )

                async with semaphore:

                    try:
                        async with client_session.request(
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

                    except Exception as e:
                        return BatchResult(resource, exception(str(e)))

            return BatchRequestHandler.create_tasks_and_sessions(
                loop, resources, request, callback
            )

        return BatchRequestHandler.batch_request(
            service=service,
            data=resources,
            task_creator=create_tasks_for_resources,
            prepare_function=prepare_function,
            callback=callback,
            **kwargs
        )

    @staticmethod
    def create_tasks_and_sessions(
            loop: AbstractEventLoop,
            elements: List[Union[str, Resource]],
            fc: Callable[[Union[str, Resource], ClientSession], Coroutine[Any, Any, Union[Resource, Action, BatchResult]]],
            callback: Optional[Callable]
    ) -> Tuple[List[asyncio.Task], List[ClientSession]]:

        tasks = []
        sessions = []

        for batch_i in BatchRequestHandler.batch(elements):

            session = ClientSession(timeout=ClientTimeout(BATCH_REQUEST_TIMEOUT_PER_REQUEST))
            sessions.append(session)

            for res in batch_i:
                prepared_request: asyncio.Task = loop.create_task(fc(res, session))

                if callback:
                    prepared_request.add_done_callback(callback)

                tasks.append(prepared_request)

        return tasks, sessions
