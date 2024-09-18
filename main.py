import logging
from logging.handlers import RotatingFileHandler
from flask import Flask, render_template, jsonify, request, redirect, url_for, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_migrate import Migrate
from azure_devops_client import AzureDevOpsClient
from database import Database
from models import User, init_db, db
import config
import json
import traceback
from functools import wraps

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'  # Change this to a secure random key
app.config['SQLALCHEMY_DATABASE_URI'] = f"postgresql://{config.PGUSER}:{config.PGPASSWORD}@{config.PGHOST}:{config.PGPORT}/{config.PGDATABASE}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

init_db(app)
migrate = Migrate(app, db)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

logging.basicConfig(level=logging.DEBUG)
handler = RotatingFileHandler('app.log', maxBytes=10000, backupCount=1)
handler.setLevel(logging.DEBUG)
app.logger.addHandler(handler)

azure_client = AzureDevOpsClient(
    instance="dev.azure.com",
    collection=config.AZURE_DEVOPS_ORG,
    personal_access_token=config.AZURE_DEVOPS_PAT
)
db_connection = Database()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            flash('You need to be an admin to access this page.', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
@login_required
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('index'))
        flash('Invalid username or password')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Username already exists')
        else:
            try:
                new_user = User(username=username, email=email)
                new_user.set_password(password)
                db.session.add(new_user)
                db.session.commit()
                flash('Registration successful')
                return redirect(url_for('login'))
            except Exception as e:
                db.session.rollback()
                app.logger.error(f"Error during registration: {str(e)}")
                flash('An error occurred during registration. Please try again.')
    return render_template('register.html')

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        current_user.username = request.form['username']
        current_user.email = request.form['email']
        if 'set_admin' in request.form:
            current_user.role = 'admin'
        else:
            current_user.role = 'user'
        db.session.commit()
        flash('Profile updated successfully')
        return redirect(url_for('profile'))
    return render_template('profile.html')

@app.route('/api/release_plan')
@login_required
def get_release_plan():
    try:
        app.logger.debug("Attempting to fetch data from cache")
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

        app.logger.debug("Caching fetched data")
        db_connection.cache_data(release_plan)

        app.logger.debug(f"API data structure: {json.dumps(release_plan, indent=2)}")
        return jsonify(release_plan)
    except Exception as e:
        error_message = f"Error in get_release_plan: {str(e)}\n{traceback.format_exc()}"
        app.logger.error(error_message)
        return jsonify({'error': str(e)}), 500

@app.route('/api/test_connection')
@login_required
@admin_required
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
