import threading
import queue
from flask import current_app
from modules.paperless_ai_titles import PaperlessAITitles


task_queue = queue.Queue()
app = current_app

def worker():
    """Worker thread to process tasks sequentially."""
    while True:
        document_id = task_queue.get()
        if document_id is None:  # Sentinel to stop the worker
            break
        with app.app_context():
            try:
                ai = PaperlessAITitles(openai_api_key, paperless_url, paperless_api_key, "settings.yaml")
                ai.generate_and_update_title(document_id)
            except Exception as e:
                app.logger.info(f"Error processing document {document_id}: {e}")
            finally:
                task_queue.task_done()

# Start the worker thread
worker_thread = threading.Thread(target=worker, daemon=True)
worker_thread.start()

def start_background_processsing(document_id):
    """Add a task to the queue for sequential processing."""
    app.logger.info(f"Queueing document ID: '{document_id}' for processing")
    task_queue.put(document_id)
    return True