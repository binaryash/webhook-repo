from flask import Blueprint, json, request, jsonify, render_template
from app.extensions import mongo_collection
from datetime import datetime, timezone 
import dateutil.parser

webhook = Blueprint('Webhook', __name__, url_prefix='/webhook')

def ordinal(n):
    return "%d%s" % (n, "tsnrhtdd"[(n//10%10!=1)*(n%10<4)*n%10::4])

def format_dt(dt):
    # Formats datetime to: "1st April 2021 - 9:30 PM UTC"
    return f"{dt.day}{ordinal(dt.day)[-2:]} {dt.strftime('%B %Y - %I:%M %p UTC')}"

@webhook.route('/receiver', methods=["POST"])
def receiver():
    event_type = request.headers.get('X-GitHub-Event')
    payload = request.json
    
    data = None

    # 1. Handle Push
    if event_type == 'push':
        author = payload.get('pusher', {}).get('name', 'Unknown')
        to_branch = payload.get('ref', '').split('/')[-1]
        req_id = payload.get('head_commit', {}).get('id', 'unknown_hash')
        
        # Parse and immediately convert to UTC
        timestamp_obj = dateutil.parser.parse(payload['head_commit']['timestamp'])
        timestamp_obj = timestamp_obj.astimezone(timezone.utc) 
        
        timestamp_str = timestamp_obj.strftime("%Y-%m-%d %H:%M:%S UTC")

        data = {
            "request_id": req_id,
            "author": author,
            "action": "PUSH",
            "from_branch": "",
            "to_branch": to_branch,
            "timestamp": timestamp_str, 
            "formatted_message": f'"{author}" pushed to "{to_branch}" on {format_dt(timestamp_obj)}'
        }

    # 2. Handle Pull Request (and Merge)
    elif event_type == 'pull_request':
        action_status = payload.get('action')
        pr = payload.get('pull_request', {})
        author = pr.get('user', {}).get('login', 'Unknown')
        from_branch = pr.get('head', {}).get('ref')
        to_branch = pr.get('base', {}).get('ref')
        
        req_id = str(pr.get('id', 'unknown_id'))

        # Parse and immediately convert to UTC
        timestamp_obj = dateutil.parser.parse(pr.get('updated_at'))
        timestamp_obj = timestamp_obj.astimezone(timezone.utc)

        timestamp_str = timestamp_obj.strftime("%Y-%m-%d %H:%M:%S UTC")

        # Merge Logic
        if action_status == 'closed' and pr.get('merged') is True:
            data = {
                "request_id": req_id,
                "author": author,
                "action": "MERGE",              
                "from_branch": from_branch,
                "to_branch": to_branch,
                "timestamp": timestamp_str,
                "formatted_message": f'"{author}" merged branch "{from_branch}" to "{to_branch}" on {format_dt(timestamp_obj)}'
            }
        # Standard PR logic
        elif action_status in ['opened', 'reopened', 'synchronize']:
            data = {
                "request_id": req_id,
                "author": author,
                "action": "PULL_REQUEST",    
                "from_branch": from_branch,
                "to_branch": to_branch,
                "timestamp": timestamp_str,
                "formatted_message": f'"{author}" submitted a pull request from "{from_branch}" to "{to_branch}" on {format_dt(timestamp_obj)}'
            }

    if data:
        mongo_collection.insert_one(data)
        return jsonify({"message": "Event stored"}), 200

    return jsonify({"message": "Event ignored"}), 200

@webhook.route('/')
def index():
    return render_template('index.html')

@webhook.route('/events')
def get_events():
    # Fetch latest 10 events.
    events = list(mongo_collection.find({}, {'_id': 0}).sort('_id', -1).limit(10))
    return jsonify(events)
