import contextlib
import logging
import time

from websockets.sync.server import serve, ServerConnection
from websockets.sync.client import connect

logger = logging.getLogger("websockets.proxy")


class ProxyServer:
    def __init__(
        self,
        upstream: str,
        time_til_pause: float,
        time_til_resume: float,
        port: int = 8080,
    ):
        self.upstream_server = upstream
        self.time_til_pause = time_til_pause
        self.time_til_resume = time_til_resume
        self.upstream_connection = None
        self.connection_time = 0
        self.shutdown_time = 0
        self.resume_time = 0
        self.port = port

    def connect(self):
        self.upstream_connection = connect(self.upstream_server)
        self.connection_time = time.time()
        self.shutdown_time = self.connection_time + self.time_til_pause
        self.resume_time = self.shutdown_time + self.time_til_resume

    def close(self):
        if self.upstream_connection:
            self.upstream_connection.close()
        with contextlib.suppress(AttributeError):
            self.server.shutdown()

    def proxy_request(self, websocket: ServerConnection):
        for message in websocket:
            self.upstream_connection.send(message)
            recd = self.upstream_connection.recv()
            current_time = time.time()
            if self.shutdown_time < current_time < self.resume_time:
                logger.info("Pausing")
                time.sleep(self.time_til_resume)
            websocket.send(recd)

    def serve(self):
        with serve(self.proxy_request, "localhost", self.port) as self.server:
            self.server.serve_forever()

    def connect_and_serve(self):
        self.connect()
        self.serve()


def run_proxy_server(time_til_pause: float = 20.0, time_til_resume: float = 30.0):
    proxy = ProxyServer("wss://archive.sub.latent.to", time_til_pause, time_til_resume)
    proxy.connect()
    proxy.serve()


if __name__ == "__main__":
    run_proxy_server()
