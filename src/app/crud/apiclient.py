from app.crud.base import CRUDRepository
from app.models.apiclient import ApiClient


class ApiClientCRUDRepository(CRUDRepository):

    @staticmethod
    def is_active_client(client: ApiClient) -> bool:
        """
        Check if an api client is active.

        Parameters:
            client (ApiClient): The api client object to check.

        Returns:
            bool: True if the api client is active, False otherwise.
        """
        return client.is_active


apiclient_crud = ApiClientCRUDRepository(model=ApiClient)