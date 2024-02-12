from collections import namedtuple
import json
import asyncio

from typing import Callable, Dict, List, Optional, Tuple, Type, Any
from typing_extensions import Unpack

from aiohttp import ClientSession

from kgforge.core.resource import Resource
from kgforge.core.commons.exceptions import RunException
from kgforge.specializations.stores.nexus.service import Service, _error_message

BatchResult = namedtuple("BatchResult", ["resource", "response"])
BatchResults = List[BatchResult]


class BatchRequestHandler:

    @staticmethod
    def batch_request(
            service: Service,
            resources: List[Resource],
            prepare_function: Callable[
                ['Service', Resource, Dict, Unpack[Any]],
                Tuple[str, str, Resource, Type[RunException], Dict, Optional[Dict], Optional[Dict]]
            ],
            callback: Callable,
            **kwargs,
    ) -> Tuple[BatchResults, BatchResults]:

        return asyncio.run(
            BatchRequestHandler.dispatch_action(
                service=service,
                data=resources,
                prepare_function=prepare_function,
                f_callback=callback,
                **kwargs
            )
        )

    @staticmethod
    def create_tasks(
            service: Service,
            semaphore: asyncio.Semaphore,
            session: ClientSession,
            loop,
            data: List[Resource],
            prepare_function: Callable[
                [Service, Resource, Dict, Unpack[Any]],
                Tuple[str, str, Resource, Type[RunException], Dict, Optional[Dict], Optional[Dict]]
            ],
            f_callback: Callable,
            **kwargs
    ) -> List[asyncio.Task]:

        def init_task(res: Resource):
            # the action specific part
            method, url, resource, exception, headers, params_, payload = prepare_function(
                service, res, **kwargs
            )

            prepared_request = loop.create_task(
                BatchRequestHandler.queue(
                    method=method,
                    semaphore=semaphore,
                    session=session,
                    url=url,
                    resource=resource,
                    exception=exception,
                    headers=headers,
                    payload=payload,
                    params=params_
                )
            )

            if f_callback:
                prepared_request.add_done_callback(f_callback)

            return prepared_request

        return [init_task(res) for res in data]

    @staticmethod
    async def dispatch_action(
            service: Service,
            data: List[Resource],
            prepare_function: Callable[
                [Service, Resource, Dict, Unpack[Any]],
                Tuple[str, str, Resource, Type[RunException], Dict, Optional[Dict], Optional[Dict]]
            ],
            f_callback: Callable,
            **kwargs
    ):
        semaphore = asyncio.Semaphore(service.max_connection)
        loop = asyncio.get_event_loop()
        async with ClientSession() as session:
            tasks = BatchRequestHandler.create_tasks(
                service=service,
                semaphore=semaphore,
                session=session,
                loop=loop,
                data=data,
                prepare_function=prepare_function,
                f_callback=f_callback,
                **kwargs
            )
            return await asyncio.gather(*tasks)

    @staticmethod
    async def queue(
            method,
            semaphore,
            session,
            url,
            resource,
            exception,
            headers,
            payload=None,
            params=None,
    ):
        async with semaphore:
            return await BatchRequestHandler.request(
                method=method,
                session=session,
                url=url,
                resource=resource,
                payload=payload,
                params=params,
                exception=exception,
                headers=headers
            )

    @staticmethod
    async def request(
            method: str,
            session: ClientSession,
            url: str,
            resource: Optional[Resource],
            payload: Optional[Dict],
            params: Optional[Dict],
            exception: Type[RunException],
            headers: Dict
    ):
        async with session.request(
                method,
                url,
                headers=headers,
                data=json.dumps(payload),
                params=params,
        ) as response:
            content = await response.json()
            if response.status < 400:
                return BatchResult(resource, content)

            error = exception(_error_message(content))
            return BatchResult(resource, error)
