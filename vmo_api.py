from station_controller import StationController
from datetime import datetime
from requests import post, Response
from os import remove


class API:
    def get_response(self, response: Response) -> dict:
        """
        Returns the response from the API.
        Args:
            response: The response from the API.
        Raises:
            Exception: If the response is not successful.
        Returns:
            The response from the API.
        """
        if response.status_code != 200:
            raise Exception("API response was not successful.")
        
        response = response.json()
        
        return response
    
    async def upload_clip(
        self, file_path: str, file_time: datetime, config: StationController.Config
    ):
        """
        Uploads a clip to the specified endpoint.
        Args:
            file_path (str): The path of the file to be uploaded.
            file_time (datetime): The date and time associated with the file.
            config (StationController.Config): The configuration object.
        Raises:
            Exception: If the upload fails.
        Returns:
            None
        """
        files = {"clip": open(file_path, "rb")}
        # Send date time in ISO format
        # Convert to ISO format
        iso_format_datetime = file_time.isoformat()

        data = {"dt_iso": iso_format_datetime, "source": config.STATION_SRC_ID}

        # Create the request and collect the response
        jsonResponse = self.get_response(post(config.UPLOAD_ENDPOINT, files=files, data=data))

        # Basic checks for errors
        if 'error' in jsonResponse:
            raise Exception("Upload failed! Error: " + jsonResponse['error'])
        if 'status' not in jsonResponse:
            raise Exception("Upload failed! Response: ", jsonResponse)
        
        # Remove the file after upload
        remove(file_path)
        return None
