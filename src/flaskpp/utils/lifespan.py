from typing import Callable, Awaitable, Dict

ASGIApp = Callable[[Dict, Callable, Callable], Awaitable[None]]


class LifespanWrapper:
    def __init__(self, app: ASGIApp, on_shutdown: Callable, on_startup: Callable):
        self.app = app
        self.on_shutdown = on_shutdown
        self.on_startup = on_startup

    async def __call__(self, scope, receive, send):
        if scope["type"] == "lifespan":
            while True:
                message = await receive()

                if message["type"] == "lifespan.startup":
                    if self.on_startup:
                        await self.on_startup()
                    await send({"type": "lifespan.startup.complete"})

                elif message["type"] == "lifespan.shutdown":
                    if self.on_shutdown:
                        await self.on_shutdown()
                    await send({"type": "lifespan.shutdown.complete"})
                    return
        else:
            await self.app(scope, receive, send)
