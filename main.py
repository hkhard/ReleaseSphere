import logging
from logging.handlers import RotatingFileHandler
from flask import Flask, render_template, jsonify
from azure_devops_client import AzureDevOpsClient
from database import Database
import config
import json
import traceback

app = Flask(__name__)

logging.basicConfig(level=logging.DEBUG)
handler = RotatingFileHandler('app.log', maxBytes=10000, backupCount=1)
handler.setLevel(logging.DEBUG)
app.logger.addHandler(handler)

azure_client = AzureDevOpsClient(
    instance="dev.azure.com",
    collection=config.AZURE_DEVOPS_ORG,
    personal_access_token=config.AZURE_DEVOPS_PAT
)
db = Database()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/release_plan')
def get_release_plan():
    try:
        # Try to fetch data from the cache first
        app.logger.debug("Attempting to fetch data from cache")
        # cached_data = db.get_cached_data()
        # if cached_data:
        #     app.logger.debug(f"Cached data structure: {json.dumps(cached_data, indent=2)}")
        #     return jsonify(cached_data)

        # If not in cache, fetch from Azure DevOps API
        app.logger.debug("Cache miss. Fetching data from Azure DevOps API")

        app.logger.debug("Starting API calls to Azure DevOps")
        app.logger.debug(f"Azure DevOps Organization: {config.AZURE_DEVOPS_ORG}")
        app.logger.debug(f"Azure DevOps Project: {config.AZURE_DEVOPS_PROJECT}")
        app.logger.debug("Personal Access Token: [REDACTED]")

        app.logger.debug("Fetching epics from Azure DevOps")
        epics = azure_client.get_work_items(config.AZURE_DEVOPS_PROJECT, 'Epic')
        app.logger.debug(f"Fetched {len(epics)} epics")
        app.logger.debug(f"Raw epics response: {json.dumps(epics, indent=2)}")

        app.logger.debug("Fetching features from Azure DevOps")
        features = azure_client.get_work_items(config.AZURE_DEVOPS_PROJECT, 'Feature')
        app.logger.debug(f"Fetched {len(features)} features")
        app.logger.debug(f"Raw features response: {json.dumps(features, indent=2)}")

        app.logger.debug("Fetching sprints from Azure DevOps")
        sprints = azure_client.get_sprints(config.AZURE_DEVOPS_PROJECT)
        app.logger.debug(f"Fetched {len(sprints)} sprints")
        app.logger.debug(f"Raw sprints response: {json.dumps(sprints, indent=2)}")

        release_plan = {
            'epics': epics,
            'features': features,
            'sprints': sprints
        }

        # Cache the fetched data
        app.logger.debug("Caching fetched data")
        db.cache_data(release_plan)

        app.logger.debug(f"API data structure: {json.dumps(release_plan, indent=2)}")
        return jsonify(release_plan)
    except Exception as e:
        error_message = f"Error in get_release_plan: {str(e)}\n{traceback.format_exc()}"
        app.logger.error(error_message)
        return jsonify({'error': str(e)}), 500

@app.route('/api/test_connection')
def test_azure_devops_connection():
    app.logger.debug("Testing Azure DevOps connection")
    connection_successful, message = azure_client.test_connection()
    if connection_successful:
        app.logger.debug(f"Connection to Azure DevOps successful: {message}")
        return jsonify({"status": "success", "message": message})
    else:
        app.logger.error(f"Failed to connect to Azure DevOps: {message}")
        return jsonify({"status": "error", "message": message}), 500

if __name__ != '__main__':
    gunicorn_logger = logging.getLogger('gunicorn.error')
    app.logger.handlers = gunicorn_logger.handlers
    app.logger.setLevel(gunicorn_logger.level)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
