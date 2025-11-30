from datetime import datetime

from openai import OpenAI
from dotenv import load_dotenv
from flask import current_app

import yaml
import os

load_dotenv()
openai_base_url = os.getenv("OPENAI_BASE_URL")


class OpenAITitles:
    def __init__(self, openai_api_key, settings_file="settings.yaml") -> None:
        self.__openai = OpenAI(api_key=openai_api_key, base_url=openai_base_url)
        self.settings = self.__load_settings(settings_file)
        current_app.logger.debug(f"Init with settings: {self.settings}")

    def __load_settings(self, settings_file):
        try:
            with open(settings_file, "r") as f:
                return yaml.safe_load(f)
        except Exception as e:
            current_app.logger.error(f"Error loading settings file: {e}")
            return None

    def __ask_chat_gpt(self, content, role="user"):
        try:
            res = self.__openai.chat.completions.create(
                messages=[
                    {
                        "role": role,
                        "content": content,
                    },
                ],
                model=self.settings.get("openai_model", "gpt-4o-mini"),
            )
            return res
        except Exception as e:
            current_app.logger.error("Error generating title from GPT: %s", e)
            return None

    def generate_title_from_text(self, text, document_id=None):
        with_date = self.settings.get("with_date", False)
        setting_prompt = self.settings.get("prompt", None)
        if setting_prompt:
            prompt = setting_prompt.get("main", "")

            if with_date:
                current_date = datetime.today().strftime("%Y-%m-%d")
                with_date_prompt = setting_prompt.get("with_date", "")
                with_date_prompt = with_date_prompt.replace(
                    "{current_date}", current_date
                )
                prompt += with_date_prompt
            else:
                prompt += setting_prompt.get("without_date", "")

            prompt += setting_prompt.get("pre_content", "") + text
            prompt += setting_prompt.get("post_content", "")

            current_app.logger.info(
                f"Starting LLM Request for document id {(document_id if document_id else "N/A")}"
            )

            result = self.__ask_chat_gpt(prompt)

            # Defensive: check result shape and extract raw content
            raw_content = None
            try:
                # SDK object style: result.choices[0].message.content
                raw_content = result.choices[0].message.content
            except Exception:
                try:
                    # dict style: result['choices'][0]['message']['content']
                    raw_content = (
                        result.get("choices", [])[0].get("message", {}).get("content")
                    )
                except Exception:
                    raw_content = None

            if not raw_content:
                return None

            current_app.logger.debug(f"Raw LLM Output: {raw_content}")

            # Extract final title from the model output using heuristics
            newTitle = self._extract_final_title_from_content(raw_content)

            current_app.logger.info(
                f"Generated Title: '{newTitle}' with model '{self.settings.get("openai_model", "gpt-4o-mini")}'"
            )

            return newTitle
        else:
            current_app.logger.warning("Prompt settings not found.")
            return None

    def _extract_final_title_from_content(self, content: str) -> str:
        if not content or not isinstance(content, str):
            current_app.logger.error(
                f"Invalid content provided for title extraction: {content}"
            )
            return ""

        # Normalize line endings and strip
        text = content.strip()

        # Split into lines and filter out 'thinking' lines
        lines = [l.rstrip() for l in text.splitlines()]
        filtered = []
        for l in lines:
            low = l.lower()
            if not l.strip():
                continue
            # remove common thinking artifacts
            if "thinking" in low or "thought" in low or l.strip().startswith("..."):
                continue
            # skip metadata-like lines
            if (
                low.startswith("assistant:")
                or low.startswith("final:")
                or low.startswith("final title")
            ):
                # keep the remainder after colon if present
                parts = l.split(":", 1)
                if len(parts) > 1 and parts[1].strip():
                    filtered.append(parts[1].strip())
                continue
            filtered.append(l.strip())

        current_app.logger.debug(
            f"Filtered LLM lines without thinking artifacts: {filtered}"
        )

        if not filtered:
            current_app.logger.warning("No valid lines found in LLM output.")
            return text

        # If the model returned multiple candidate lines, prefer the last reasonable one
        # Choose last line that is not too long (<=128 chars)
        for candidate in reversed(filtered):
            if 0 < len(candidate) <= 128:
                # strip surrounding quotes or dashes
                candidate = candidate.strip().strip('"').strip("'").strip("-").strip()
                # handle HTML-like tags: <title>...</title> or other wrappers
                try:
                    import re, html

                    # Simplified and robust logic to extract text inside <title>...</title>
                    m = re.search(
                        r"<title>(.*?)</title>",
                        candidate,
                        flags=re.IGNORECASE | re.DOTALL,
                    )
                    if m:
                        # Extract and clean the inner text
                        candidate = m.group(1).strip()

                    current_app.logger.info("Extracted candidate title: %s", candidate)

                    # Unescape HTML entities
                    return html.unescape(candidate)
                except Exception as e:
                    current_app.logger.error("Error extracting title: %s", e)
                    return candidate

        # Fallback to the last filtered line
        current_app.logger.info("Falling back to last filtered line.")
        return filtered[-1].strip()
