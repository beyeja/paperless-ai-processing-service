import requests
from flask import current_app

from modules.openai_titles import OpenAITitles

app = current_app

class PaperlessAITitles:
    def __init__(self, openai_api_key, paperless_url, paperless_api_key, settings_file="settings.yaml"):
        self.openai_api_key = openai_api_key
        self.paperless_url = paperless_url
        self.paperless_api_key = paperless_api_key
        self.ai = OpenAITitles(self.openai_api_key, settings_file)


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
                "Failed to get document details from paperless-ngx. Status code: %s", response.status_code
            )
            app.logger.error(response.text)
            return None


    def __update_document_title(self, document_id, new_title):
        payload = {"title": new_title.strip()[:128]}

        headers = {
            "Authorization": f"Token {self.paperless_api_key}",
            "Content-Type": "application/json",
        }

        response = requests.patch(
            f"{self.paperless_url}/documents/{document_id}/",
            json=payload,
            headers=headers,
        )

        if response.status_code == 200:
            app.logger.info(
                "Title of %s successfully updated in paperless-ngx to %s.", document_id, new_title
            )
        else:
            app.logger.error(
                "Failed to update title in paperless-ngx. Status code: %s", response.status_code
            )
            app.logger.error(response.text)


    def generate_and_update_title(self, document_id):
        document_details = self.__get_document_details(document_id)
        if document_details:
            app.logger.info("Current Document Title: %s", document_details['title'])

            content = document_details.get("content", "")

            app.logger.info("all document details: ", document_details)

            new_title = self.ai.generate_title_from_text(content)

            if new_title:
                app.logger.info("Generated Document Title: %s", new_title)

                self.__update_document_title(document_id, new_title)
            else:
                app.logger.warning("Failed to generate the document title.")
        else:
            app.logger.warning("Failed to retrieve document details.")
