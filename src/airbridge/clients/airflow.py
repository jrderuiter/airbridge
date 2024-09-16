import logging

import httpx


class AirflowClient:

    def __init__(self, host: str, login: str, password: str, port: int=8080):
        self._host = host
        self._port = port
        self._login = login
        self._password = password

        self._logger = logging .getLogger(__name__)

    def _get_client(self):
        auth = httpx.BasicAuth(username=self._login, password=self._password)
        return httpx.AsyncClient(auth=auth)

    async def create_dataset_event(self, dataset_uri, extra=None):
        async with self._get_client() as client:
            response = await client.post(
                f'http://{self._host}:{self._port}/api/v1/datasets/events',
                json={
                    "dataset_uri": dataset_uri,
                    "extra": extra or {}
                }
            )

            if response.is_success:
                self._logger.info("Posted dataset event!")
            elif response.status_code == 404 and response.json()["title"] == "Dataset not found":
                self._logger.info(f"Dataset '{dataset_uri}' doesn't exist, skipping.")
            else:
                response.raise_for_status()
