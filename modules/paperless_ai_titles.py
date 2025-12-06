import requests
from flask import current_app
from dotenv import load_dotenv

import os

load_dotenv()
ppl_ngx_updated_tag_id = os.getenv("PAPERLESS_NGX_UPDATED_TAG_ID", None)

from modules.openai_titles import OpenAITitles

app = current_app


class PaperlessAITitles:
    def __init__(
        self,
        openai_api_key,
        paperless_url,
        paperless_api_key,
        settings_file="settings.yaml",
    ):
        self.openai_api_key = openai_api_key
        self.paperless_url = paperless_url
        self.paperless_api_key = paperless_api_key
        self.ai = OpenAITitles(self.openai_api_key, settings_file)

        # Optional: Tag ID to mark updated documents
        self.updatedTagId = ppl_ngx_updated_tag_id

    def __get_document_details(self, document_id):
        headers = {
            "Authorization": f"Token {self.paperless_api_key}",
            "Content-Type": "application/json",
        }

        response = requests.get(
            f"{self.paperless_url}/documents/{document_id}/", headers=headers
        )

        if response.status_code == 200:
            return response.json()
        else:
            app.logger.error(
                f"Failed to get document details from paperless-ngx. Status code: {response.status_code}"
            )
            app.logger.error(response.text)
            return None

    def __add_updated_tag(self, document_id):
        url = f"{self.paperless_url}/documents/bulk_edit/"

        headers = {
            "Authorization": f"Token {self.paperless_api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "documents": [document_id],
            "method": "add_tag",
            "parameters": {"tag": self.updatedTagId},
        }

        app.logger.debug(
            f"Adding updated tag to document {document_id} with payload {payload}"
        )

        response = requests.post(
            url,
            json=payload,
            headers=headers,
        )

        if response.status_code == 200:
            app.logger.info(
                f"Added tag:'{self.updatedTagId}' successfully to doc {document_id} in paperless-ngx.",
            )
        else:
            app.logger.error(
                f"Failed to add updated tag in paperless-ngx. Status code: {response.status_code}",
            )
            app.logger.error(response.text)

    def __update_document_title(self, document_id, new_title):
        payload = {"title": new_title.strip()[:128]}

        url = f"{self.paperless_url}/documents/{document_id}/"

        headers = {
            "Authorization": f"Token {self.paperless_api_key}",
            "Content-Type": "application/json",
        }

        app.logger.info(f"Updating document: url {url} with payload {payload}")

        response = requests.patch(
            url,
            json=payload,
            headers=headers,
        )

        if response.status_code == 200:
            app.logger.info(
                f"Title of doc {document_id} successfully updated in paperless-ngx to {new_title}.",
            )
        else:
            app.logger.error(
                f"Failed to update title in paperless-ngx. Status code: {response.status_code}",
            )
            app.logger.error(response.text)

    def generate_and_update_title(self, document_id):
        document_details = self.__get_document_details(document_id)
        if document_details:
            app.logger.debug(
                f"Current Document Title: { document_details["title"]}",
            )

            content = document_details.get("content", "")

            app.logger.debug(f"all document details: {document_details}")

            new_title = self.ai.generate_title_from_text(
                content, document_id=document_id
            )

            if new_title:
                app.logger.info(
                    f"Generated Title. id '{document_id}' old title '{document_details['title']}' new title '{new_title}'"
                )

                self.__update_document_title(document_id, new_title)

                # Add updated tag if configured
                if self.updatedTagId:
                    self.__add_updated_tag(document_id)

            else:
                app.logger.error(
                    f"Failed to generate new title for document id {document_id}, no title returned from LLM"
                )
        else:
            app.logger.error(
                f"Failed to retrieve document details for document id {document_id}"
            )
