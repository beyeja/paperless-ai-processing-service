#!/usr/bin/env python3

import os
from flask import Flask, request, jsonify
from dotenv import load_dotenv
import logging

from modules.server_utils import start_background_processsing

load_dotenv()
paperless_url = os.getenv("PAPERLESS_NGX_URL")
paperless_api_key = os.getenv("PAPERLESS_NGX_API_KEY")
openai_api_key = os.getenv("OPENAI_API_KEY")

# Initialize Flask app
app = Flask(__name__)

# Set logging format for better readability, especially in containers
logging.basicConfig(
    level=logging.INFO, # Log only INFO level messages and higher
    format='[%(asctime)s] %(levelname)s in %(module)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

app.logger.info("Starting Paperless AI Titles Webhook Service. Serving...")

@app.route('/health', methods=['GET'])
def health_check():
    """Returns a simple success message for the health probe."""
    return jsonify({
        "status": "ok",
        "service": "Paperless Webhook Service"
    }), 200

@app.route('/document/changed', methods=['POST'])
def paperless_webhook():    
    """"""
    try:
        # Paperless-ngx sends a JSON payload on the 'Document Updated' event
        data = request.get_json(silent=True)
        app.logger.info(f"json payload: {data}")

        # The document ID is nested in the 'document' object
        document_url = data.get('url', '');
        # remove trailing slash and get last part as document ID
        document_id = document_url.rstrip('/').split('/')[-1] if document_url else None
        
        if document_id:
            if start_background_processsing(document_id):
                return jsonify({'status': 'Processing started'}), 200
            else:
                app.logger.info(f"Processing failed for document ID: {document_id}")
                return jsonify({'status': 'Processing failed'}), 500
        
        app.logger.info("No document ID found in the request")
        return jsonify({'status': 'Missing document ID'}), 400
    
    except Exception as e:
        app.logger.info(f"Error handling webhook request: {e}")
        return jsonify({'status': 'Invalid request', 'error': str(e)}), 400
    

# To run the app
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)