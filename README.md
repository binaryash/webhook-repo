# GitHub Webhook Event Receiver

This application serves as a middleware system designed to ingest, normalize, and visualize high-frequency events from GitHub repositories. It exposes a public webhook endpoint to capture `Push` and `Pull Request` events, persists them into a MongoDB datastore with a structured schema, and provides a front-end dashboard that updates in near real-time via client-side polling.

## Architecture

The system follows a producer-consumer pattern:

1. **Ingestion Layer:** A Flask REST API receives `POST` payloads from GitHub Webhooks.
2. **Processing Layer:** The application validates headers, parses the JSON payload, determines the event type (Push, PR Open, or Merge), and formats the timestamp to UTC.
3. **Persistence Layer:** Parsed events are stored in a MongoDB collection with a strict schema including `request_id`, `author`, `action`, and `timestamp`.
4. **Presentation Layer:** A lightweight HTML/JS frontend polls the internal API every 15 seconds to fetch and render the latest repository activities.

## Technology Stack

* **Backend:** Python 3, Flask
* **Database:** MongoDB
* **Utilities:** `pymongo` for database interactions, `python-dateutil` for ISO 8601 parsing.
* **Frontend:** Vanilla JavaScript (ES6+), HTML5, CSS3.

## Prerequisites

* Python 3.8+
* MongoDB (running locally on default port `27017` or via Docker)

## Installation & Setup

### 1. Clone the Repository

```bash
git clone <repository-url>
cd webhook-repo

```

### 2. Configure the Environment

Create a virtual environment to isolate dependencies.

```bash
# Linux/MacOS
python3 -m venv venv
source venv/bin/activate

# Windows
python -m venv venv
venv\Scripts\activate

```

### 3. Install Dependencies

```bash
pip install -r requirements.txt

```

### 4. Database Initialization

Ensure a MongoDB instance is running. If using Docker:

```bash
docker run -d -p 27017:27017 --name mongo-db mongo:latest

```

The application will automatically create the `github_events` database and `actions` collection upon the first write operation.

## Usage

### Starting the Server

Execute the entry point script to start the Flask development server.

```bash
python run.py

```

The application will start on `http://127.0.0.1:5000`.

### Exposing to the Internet

To receive webhooks from GitHub, the local server must be exposed via a tunneling service such as Ngrok.

```bash
ngrok http 5000

```

Use the generated HTTPS URL to configure the GitHub Webhook settings.

## API Endpoints

### 1. Webhook Receiver

* **Endpoint:** `POST /webhook/receiver`
* **Description:** Accepts JSON payloads from GitHub.
* **Supported Events:** `push`, `pull_request`.
* **Logic:**
* Detects `push` events and records author, branch, and commit hash.
* Detects `pull_request` events.
* Identifies `merge` actions by checking if the pull request is closed and the `merged` flag is true.



### 2. Event Stream

* **Endpoint:** `GET /webhook/events`
* **Description:** Returns the 10 most recent events sorted by timestamp (descending).
* **Response Format:** JSON array of event objects.

### 3. Dashboard

* **Endpoint:** `GET /webhook/`
* **Description:** Renders the monitoring interface.

## Database Schema

Events are stored in the `actions` collection with the following structure:

| Field | Type | Description |
| --- | --- | --- |
| `request_id` | String | Commit Hash (for Push) or PR ID (for PRs) |
| `author` | String | GitHub username of the actor |
| `action` | String | Enum: `PUSH`, `PULL_REQUEST`, `MERGE` |
| `from_branch` | String | Source branch (empty for Push) |
| `to_branch` | String | Target branch |
| `timestamp` | String | UTC datetime string |
| `formatted_message` | String | Human-readable event description |
