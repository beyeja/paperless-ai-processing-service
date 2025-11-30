import threading
import queue
from dotenv import load_dotenv
import os

from flask import current_app
from modules.paperless_ai_titles import PaperlessAITitles

load_dotenv()
paperless_url = os.getenv("PAPERLESS_NGX_URL")
paperless_api_key = os.getenv("PAPERLESS_NGX_API_KEY")
openai_api_key = os.getenv("OPENAI_API_KEY")

task_queue = queue.Queue()


def worker(app):
    """Worker thread to process tasks sequentially."""
    while True:
        document_id = task_queue.get()
        if document_id is None:  # Sentinel to stop the worker
            break
        with app.app_context():
            try:
                ai = PaperlessAITitles(
                    openai_api_key, paperless_url, paperless_api_key, "settings.yaml"
                )
                ai.generate_and_update_title(document_id)
            except Exception as e:
                current_app.logger.info(f"Error processing document {document_id}: {e}")
            finally:
                task_queue.task_done()


def start_worker_thread(app):
    """Function to create and start the worker thread. passes the Flask app context."""
    worker_thread = threading.Thread(target=worker, args=(app,), daemon=True)
    worker_thread.start()
    return worker_thread
