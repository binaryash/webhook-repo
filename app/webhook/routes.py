from flask import Blueprint, json, request, jsonify, render_template
from app.extensions import mongo_collection
from datetime import datetime
import dateutil.parser

webhook = Blueprint('Webhook', __name__, url_prefix='/webhook')

# Helper Functions for Formatting
def ordinal(n):
    return "%d%s" % (n, "tsnrhtdd"[(n//10%10!=1)*(n%10<4)*n%10::4])

def format_dt(dt):
    # Formats datetime to: "1st April 2021 - 9:30 PM UTC"
    suffix = ordinal(dt.day)
    date_str = dt.strftime(f"{suffix} %B %Y - %I:%M %p UTC")
    # Clean up standard strftime result to match exact requirement
    return f"{dt.day}{ordinal(dt.day)[-2:]} {dt.strftime('%B %Y - %I:%M %p UTC')}"

# The Webhook Receiver (POST)
@webhook.route('/receiver', methods=["POST"])
def receiver():
    event_type = request.headers.get('X-GitHub-Event')
    payload = request.json

    data = None

    # 1. Handle PUSH
    if event_type == 'push':
        author = payload.get('pusher', {}).get('name', 'Unknown')
        to_branch = payload.get('ref', '').split('/')[-1]
        timestamp = dateutil.parser.parse(payload['head_commit']['timestamp'])
        
        data = {
            "type": "PUSH",
            "author": author,
            "to_branch": to_branch,
            "timestamp": timestamp,
            "formatted_message": f'"{author}" pushed to "{to_branch}" on {format_dt(timestamp)}'
        }

    # 2. Handle PULL REQUEST (and MERGE)
    elif event_type == 'pull_request':
        action = payload.get('action')
        pr = payload.get('pull_request', {})
        author = pr.get('user', {}).get('login', 'Unknown')
        from_branch = pr.get('head', {}).get('ref')
        to_branch = pr.get('base', {}).get('ref')
        timestamp = dateutil.parser.parse(pr.get('updated_at'))

        # MERGE LOGIC
        if action == 'closed' and pr.get('merged') is True:
            data = {
                "type": "MERGE",
                "author": author,
                "from_branch": from_branch,
                "to_branch": to_branch,
                "timestamp": timestamp,
                "formatted_message": f'"{author}" merged branch "{from_branch}" to "{to_branch}" on {format_dt(timestamp)}'
            }
        # STANDARD PR LOGIC
        elif action in ['opened', 'reopened', 'synchronize']:
            data = {
                "type": "PULL_REQUEST",
                "author": author,
                "from_branch": from_branch,
                "to_branch": to_branch,
                "timestamp": timestamp,
                "formatted_message": f'"{author}" submitted a pull request from "{from_branch}" to "{to_branch}" on {format_dt(timestamp)}'
            }

    if data:
        mongo_collection.insert_one(data)
        return jsonify({"message": "Event stored"}), 200

    return jsonify({"message": "Event ignored"}), 200

# The UI Route
@webhook.route('/')
def index():
    return render_template('index.html')

# The Polling API
@webhook.route('/events')
def get_events():
    # Fetch latest 10 events, sorted by newest first
    events = list(mongo_collection.find({}, {'_id': 0}).sort('timestamp', -1).limit(10))
    return jsonify(events)
