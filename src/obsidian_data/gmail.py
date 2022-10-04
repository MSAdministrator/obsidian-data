"""Retrieves emails from gmail using their API."""
import os
import pickle
from typing import Dict, List
from base64 import b64decode

from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from prompt_toolkit.shortcuts import ProgressBar
from prompt_toolkit.formatted_text import HTML

from .base import Base


class Gmail(Base):
    """Connects and retrieves emails from Gmail using the API."""

    SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
    MAX_RESULTS = 500

    def __init__(self, credentials: str = "credentials.json", pickle_file: str = None, total_max_results: int = MAX_RESULTS) -> None:
        """Retrieve emails using the provided credentials or pickle file.

        Args:
            credentials (str, optional): The path to a credentials.json file. Defaults to "credentials.json".
            pickle_file (str, optional): A pickle file of credentials session. Defaults to None.
            total_max_results (int, optional): The total max results after pagination. Defaults to 500.
        """
        self.total_max_results = total_max_results
        self.message_id_list = []
        self._credentials = self.get_abs_path(credentials)
        if not os.path.exists(self._credentials):
            raise Exception()
        self.__creds = self._get_creds_from_pickle_file(pickle_file=pickle_file)
        # Connect to the Gmail API
        self.service = build('gmail', 'v1', credentials=self.__creds)

    def _create_pickle_file(self, pickle_file: str, creds: Credentials) -> Credentials:
        """Creates a pickle file on disk.

        Args:
            pickle_file (str): The pickle file name and path on disk.
            creds (Credentials): The credentials data to save to disk.

        Returns:
            Credentials: A parsed credentials object used for authentication to Gmail API.
        """
        if not os.path.exists(pickle_file):
            os.makedirs(pickle_file)
        with open(pickle_file, "wb") as token:
            pickle.dump(creds, token)
        return creds

    def _load_pickle_file(self, pickle_file: str) -> Credentials:
        """Loads the provided pickle file path and returns a Credentials object.

        Args:
            pickle_file (str): The path to the pickle file on disk.

        Returns:
            Credentials: A Credentials object used for authentication to Gmail API.
        """
        with open(pickle_file, "rb") as token:
            return pickle.load(token)

    def _get_pickle_file(self, pickle_file: str) -> Credentials:
        """Retrieves a pickle file or attempts to find one on disk.

        Args:
            pickle_file (str): The path of a pickle file.

        Returns:
            Credentials: A Credentials object used for authentication to Gmail API.
        """
        if not pickle_file:
            pickle_file = os.path.join(os.path.dirname(self._credentials), "token.pickle")
            if os.path.exists(pickle_file):
                return self._load_pickle_file(pickle_file=pickle_file)
        else:
            pickle_file = self.get_abs_path(pickle_file)
            if os.path.exists(pickle_file):
                return self._load_pickle_file(pickle_file=pickle_file)
        return None

    def _get_creds_from_pickle_file(self, pickle_file: str = None) -> Credentials:
        """Returns the provided pickle file or attempts to create a new one.

        Args:
            pickle_file (str, optional): A path to a pickle file. Defaults to None.

        Returns:
            Credentials: A Credentials object used for authentication to Gmail API.
        """
        creds = self._get_pickle_file(pickle_file=pickle_file)
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(self._credentials, self.SCOPES)
                creds = flow.run_local_server(port=0)
            pickle_file = os.path.join(os.path.dirname(self._credentials), "token.pickle")
            creds = self._create_pickle_file(pickle_file=pickle_file, creds=creds)
        return creds

    def get_message_id_list(self, query: str = None, next_page_token: str = None) -> List[str]:
        """Returns a list of message IDs from gmail based on a query.

        Args:
            query (str, optional): A query string. Defaults to None.
            next_page_token (str, optional): A pageToken for pagination. Defaults to None.

        Returns:
            List[str]: Returns a list of message IDs.
        """
        parameter_dict = {"userId": "me", "maxResults": self.MAX_RESULTS}
        if next_page_token:
            parameter_dict.update({
                "pageToken": next_page_token
            })
        if query:
            parameter_dict.update({"q": query})
        result = self.service.users().messages().list(**parameter_dict).execute()
        messages = result.get('messages')
        for msg in messages:
            if len(self.message_id_list) <= self.total_max_results:
                self.message_id_list.append(msg["id"])
            else:
                return self.message_id_list
        if result.get("nextPageToken"):
            self.__logger.debug(f"Current count of message ids is {len(self.message_id_list)}")
            self.get_message_id_list(query=query, next_page_token=result["nextPageToken"])

    def _get_subject(self, payload: dict) -> str:
        """Returns the subject from a given payload.

        Args:
            payload (dict): A message payload object.

        Returns:
            str: The subject of a message.
        """
        if payload and payload.get("headers"):
            for item in payload["headers"]:
                if item.get("name") and item["name"] == "Subject":
                    return item.get("value")

    def _get_attachment_content(self, message_id: str, attachment_id: str) -> str:
        response = self.service.users().messages().attachments().get(
            userId="me", messageId=message_id, id=attachment_id
        ).execute()
        if response and response.get("data"):
            return response["data"]

    def _decode_data(self, data) -> str:
        return b64decode(data).decode(encoding="utf-8").strip()

    def _get_attachment(self, message_id: str, payload: dict) -> str:
        attachment_list = []
        if payload and payload.get("parts"):
            if isinstance(payload["parts"], list):
                for part in payload["parts"]:
                    if part and part.get("body") and part["body"].get("attachmentId"):
                        attachment_id = part["body"]["attachmentId"]
                        attachment_name = None
                        if part.get("headers"):
                            for header in part["headers"]:
                                if header.get("value") and "attachment; filename=" in header["value"]:
                                    attachment_name = header["value"].split("attachment; filename=\"")[-1].strip()
                        attachment_list.append({
                            "name": attachment_name if attachment_name else "unknown",
                            "data": self._get_attachment_content(message_id=message_id, attachment_id=attachment_id)
                        })
        return attachment_list

    def _get_body(self, payload: dict) -> str:
        """Returns the decoded message body.

        Args:
            payload (dict): A message payload object.

        Returns:
            str: The body of a message.
        """
        if payload and payload.get("body") and payload["body"].get("data"):
            data = payload["body"]["data"]
            data = data.replace("-","+").replace("_","/")
            return b64decode(data).decode(encoding="utf-8").strip()
        elif payload and payload.get("parts"):
            body_string = ""
            if isinstance(payload["parts"], list):
                for part in payload["parts"]:
                    if part and part.get("body") and part["body"].get("data"):
                        data = part["body"]["data"]
                        data = data.replace("-","+").replace("_","/")
                        body_string += b64decode(data).decode(encoding="utf-8").strip()
                        body_string += "\n"
                return body_string

    def get_messages(self, query: str = None, include_attachments: bool = True) -> List[Dict[str, str]]:
        """Returns the subject and the body of all messages based on a query.

        Args:
            query (str, optional): A query string. Defaults to None.
            include_attachments (bool, optional): Whether or not to include attachments. Defaults to True.

        Returns:
            List[Dict[str, str]]: Returns a list of dicts containing a subject and body.
        """
        return_list = []
        temp_list = []
        if not self.message_id_list:
            self.get_message_id_list(query=query)
        title = HTML(f'Processing <style bg="yellow" fg="black">{len(self.message_id_list)} emails...</style>')
        with ProgressBar(title=title) as pb:
            for item in pb(self.message_id_list):
                text = self.service.users().messages().get(userId="me", id=item).execute()
                temp_list.append(text)
            
                try:
                    if text.get("payload") and text["payload"]:
                        return_dict = {
                            "subject": self._get_subject(payload=text["payload"]),
                            "body": self._get_body(payload=text["payload"]),
                        }
                        if include_attachments:
                            return_dict.update({
                                "attachments": self._get_attachment(message_id=item, payload=text["payload"])
                            })
                        return_list.append(return_dict)
                except Exception as e:
                    self.__logger.error(f"An exception has occurred: {e}")
        return return_list
