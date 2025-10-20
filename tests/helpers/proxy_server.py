import asyncio

from websockets.asyncio.server import serve, ServerConnection
from websockets.asyncio.client import connect


class ProxyServer:
    def __init__(self, upstream: str, time_til_pause: float, time_til_resume: float):
        self.upstream_server = upstream
        self.time_til_pause = time_til_pause
        self.time_til_resume = time_til_resume
        self.upstream_connection = None
        self.connection_time = 0
        self.shutdown_time = 0
        self.resume_time = 0

    async def connect(self):
        self.upstream_connection = await connect(self.upstream_server)
        self.connection_time = asyncio.get_running_loop().time()
        self.shutdown_time = self.connection_time + self.time_til_pause
        self.resume_time = self.shutdown_time + self.time_til_resume

    async def close(self):
        if self.upstream_connection:
            await self.upstream_connection.close()

    async def proxy_request(self, websocket: ServerConnection):
        async for message in websocket:
            print(websocket)
            await self.upstream_connection.send(message)
            recd = await self.upstream_connection.recv()
            current_time = asyncio.get_running_loop().time()
            if self.shutdown_time < current_time < self.resume_time:
                print("Pausing")
                await asyncio.sleep(self.time_til_resume)
            await websocket.send(recd)
            # await websocket.send(message)

    async def serve(self):
        async with serve(self.proxy_request, "localhost", 8080) as server:
            await server.serve_forever()


async def main():
    proxy = ProxyServer("wss://archive.sub.latent.to", 20, 30)
    await proxy.connect()
    await proxy.serve()


if __name__ == "__main__":
    asyncio.run(main())
