#!/usr/bin/env python3

import os
from flask import Flask, request, jsonify
import logging

# Initialize Flask app
app = Flask(__name__)

from modules.server_utils import task_queue, start_worker_thread

# Set the logging level from an environment variable, defaulting to INFO
log_level = os.getenv("LOG_LEVEL", "INFO").upper()

# Configure the root logger
logging.basicConfig(
    level=getattr(logging, log_level, logging.INFO),
    format="[%(asctime)s] %(levelname)s in %(module)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

# Align Flask's logger with the root logger
app.logger.setLevel(getattr(logging, log_level, logging.INFO))

app.logger.info(f"Loglevel set to {log_level}")
app.logger.debug(f"Logging configuration: {logging.getLogger().handlers}")
app.logger.info("Starting Paperless AI Webhook Service. Serving...")


def start_background_processsing(document_id):
    """Add a task to the queue for sequential processing."""
    app.logger.info(f"Queueing document ID: '{document_id}' for processing")
    task_queue.put(document_id)
    return True


@app.route("/health", methods=["GET"])
def health_check():
    """Returns a simple success message for the health probe."""
    return jsonify({"status": "ok", "service": "Paperless Webhook Service"}), 200


@app.route("/document/changed", methods=["POST"])
def paperless_webhook():
    """"""
    try:
        # Paperless-ngx sends a JSON payload on the 'Document Updated' event
        data = request.get_json(silent=True)
        app.logger.info(f"received document changed request: {data}")

        # The document ID is nested in the 'document' object
        document_url = data.get("url", "")
        # remove trailing slash and get last part as document ID
        document_id = document_url.rstrip("/").split("/")[-1] if document_url else None

        if document_id:
            if start_background_processsing(document_id):
                return jsonify({"status": "Processing started"}), 200
            else:
                app.logger.info(f"Processing failed for document ID: {document_id}")
                return jsonify({"status": "Processing failed"}), 500

        app.logger.info("No document ID found in the request")
        return jsonify({"status": "Missing document ID"}), 400

    except Exception as e:
        app.logger.info(f"Error handling webhook request: {e}")
        return jsonify({"status": "Invalid request", "error": str(e)}), 400


# start_background_processsing(940)

# To run the app
if __name__ == "__main__":
    start_worker_thread(app)
    app.run(host="0.0.0.0", port=5000)
