# Event Manager API

A REST API for managing events, participants, and event registrations.

This project is developed with **Python** and **FastAPI** and uses **SQLite** for data persistence. It is designed as a practical software engineering project and will later be used with tools such as Git, Docker, and CI/CD.

## 1. Project Description

The **Event Manager API** allows users to:

* Create and manage events
* Register participants
* Search for events
* Manage participant information
* Register participants for events
* View participants registered for an event
* Enforce business rules related to events and registrations

The API provides an interactive Swagger interface for testing and exploring the available endpoints.

## 2. Technologies

The project uses:

* **Python**
* **FastAPI** — REST API framework
* **SQLAlchemy** — ORM for database access
* **SQLite** — relational database
* **Pydantic** — data validation
* **Uvicorn** — ASGI server
* **Pytest** — testing framework
* **HTTPX** — HTTP client used with the testing environment

## 3. Project Structure

```text
EventManager/
│
├── .gitignore
├── README.md
├── requirements.txt
│
└── app/
    ├── __init__.py
    ├── main.py
    ├── database.py
    ├── models.py
    ├── schemas.py
    │
    └── routers/
        ├── __init__.py
        ├── events.py
        ├── participants.py
        └── registrations.py
```

### Main components

**`app/main.py`**

Creates the FastAPI application and registers the API routers.

**`app/database.py`**

Configures the SQLite database and SQLAlchemy database sessions.

**`app/models.py`**

Defines the database models:

* Event
* Participant
* Registration

**`app/schemas.py`**

Defines the Pydantic schemas used for request validation and API responses.

**`app/routers/`**

Contains the API endpoints organized by functionality:

* Events
* Participants
* Registrations

## 4. Installation and Execution

### Prerequisites

Make sure the following are installed:

* Python 3.10 or later
* Git

### Clone the repository

```bash
git clone https://github.com/smaaliSahar/EventManager.git
cd EventManager
```

### Create a virtual environment

On Windows:

```bash
python -m venv .venv
```

Activate it:

```bash
.venv\Scripts\activate
```

On Linux/macOS:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### Install dependencies

```bash
pip install -r requirements.txt
```

### Start the application

```bash
uvicorn app.main:app --reload
```

The API will be available at:

```text
http://127.0.0.1:8000
```

## 5. API Documentation

FastAPI automatically generates interactive API documentation.

### Swagger UI

Open:

```text
http://127.0.0.1:8000/docs
```

Swagger allows you to:

* View all available endpoints
* Inspect request and response schemas
* Send HTTP requests
* Test the API interactively

### ReDoc

An alternative API documentation interface is available at:

```text
http://127.0.0.1:8000/redoc
```

## 6. API Endpoints

### Events

| Method | Endpoint              | Description            |
| ------ | --------------------- | ---------------------- |
| POST   | `/events/`            | Create an event        |
| GET    | `/events/`            | List all events        |
| GET    | `/events/?search=...` | Search events by title |
| GET    | `/events/{event_id}`  | Get an event           |
| PUT    | `/events/{event_id}`  | Update an event        |
| DELETE | `/events/{event_id}`  | Delete an event        |

### Participants

| Method | Endpoint                         | Description          |
| ------ | -------------------------------- | -------------------- |
| POST   | `/participants/`                 | Create a participant |
| GET    | `/participants/`                 | List participants    |
| GET    | `/participants/{participant_id}` | Get a participant    |
| DELETE | `/participants/{participant_id}` | Delete a participant |

### Registrations

| Method | Endpoint                                       | Description                               |
| ------ | ---------------------------------------------- | ----------------------------------------- |
| POST   | `/events/{event_id}/register/{participant_id}` | Register a participant for an event       |
| GET    | `/events/{event_id}/participants`              | List participants registered for an event |

## 7. Business Rules

The application enforces several business rules.

### Events

* An event title is required.
* An event title must contain at least 3 characters.
* An event location is required.
* The event date cannot be in the past.
* Event capacity must be greater than zero.
* Event capacity cannot exceed 10,000.

### Participants

* A participant name is required.
* A participant name must contain at least 2 characters.
* A participant must provide a valid email address.
* Each email address must be unique.

### Registrations

* The event must exist.
* The participant must exist.
* A participant cannot register for the same event more than once.
* An event cannot accept registrations after reaching its capacity.

### Database relationships

An event can have multiple registrations, and a participant can register for multiple events.

When an event or participant is deleted, its associated registrations are also removed.

## 8. Database

The application uses **SQLite**.

The database file is created automatically when the application starts:

```text
events.db
```

The database file is excluded from Git through `.gitignore`.

This means that each local installation of the application can have its own database.

## 9. Error Handling

The API returns appropriate HTTP status codes for common error situations.

Examples include:

* `201 Created` — resource successfully created
* `200 OK` — successful request
* `204 No Content` — successful deletion
* `400 Bad Request` — invalid business rule
* `404 Not Found` — requested resource does not exist
* `409 Conflict` — operation conflicts with an existing resource or business rule

## 10. Example Workflow

A typical use of the API is:

```text
Create an Event
      ↓
Create a Participant
      ↓
Register the Participant
      ↓
View Event Participants
```

The API can be explored interactively through Swagger UI:

```text
http://127.0.0.1:8000/docs
```
