# Healthcare Backend  

A backend system for managing patient records, doctor profiles, and patient-doctor mappings using Django, Django REST Framework (DRF), and PostgreSQL with JWT authentication.

---

## Tech Stack & Prerequisites

- **Python:** 3.12+
- **Database:** PostgreSQL
- **Framework:** Django 5.x / 6.x & Django REST Framework
- **Authentication:** `djangorestframework-simplejwt`
- **Environment:** `python-dotenv`

---

## Setup & Running

### 1. Create and Activate Virtual Environment
```bash
# Windows
python -m venv .venv
.\.venv\Scripts\activate

# Linux / macOS
python3.12 -m venv .venv
source .venv/bin/activate
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure `.env`
Copy `.env.example` to `.env` and fill in your PostgreSQL credentials:
```bash
# Windows
copy .env.example .env

# Linux / macOS
cp .env.example .env
```

All secret and database variables are required. Django will raise `ImproperlyConfigured` on startup if any required variable is missing or blank:

| Variable | Required | Default | Description |
| :--- | :--- | :--- | :--- |
| `DJANGO_SECRET_KEY` | **Yes** | *None* | Secret cryptographic key |
| `POSTGRES_DB` | **Yes** | *None* | Database name |
| `POSTGRES_USER` | **Yes** | *None* | Database username |
| `POSTGRES_PASSWORD` | **Yes** | *None* | Database password |
| `POSTGRES_HOST` | **Yes** | *None* | Host (e.g., `127.0.0.1`) |
| `POSTGRES_PORT` | **Yes** | *None* | Port (e.g., `5432`) |
| `DJANGO_DEBUG` | No | `False` | Debug mode (`True`/`False`) |
| `DJANGO_ALLOWED_HOSTS` | No | `localhost,127.0.0.1` | Allowed hosts |

### 4. Create PostgreSQL Database
Ensure PostgreSQL is running, then create the database:
```bash
createdb -U postgres -h 127.0.0.1 -p 5432 healthcare_db
# or via psql:
psql -U postgres -c "CREATE DATABASE healthcare_db;"
```

### 5. Apply Migrations
```bash
python manage.py makemigrations accounts healthcare
python manage.py migrate
```

### 6. Start the Server
```bash
python manage.py runserver 127.0.0.1:8000
```
API base URL: `http://127.0.0.1:8000/`

### 7. Run Automated Tests
```bash
python manage.py test
```
Runs 36 automated unit and integration tests verifying authentication, CRUD operations, permission isolation, and mapping rules.

---

## Authentication & JWT Usage

All patient, doctor, and mapping endpoints require a JWT Bearer token in the `Authorization` header:
```text
Authorization: Bearer <access_token>
```

### 1. Register User
**Request:** `POST /api/auth/register/`
```json
{
  "name": "Dr. Alex Mercer",
  "email": "alex.mercer@healthcare.org",
  "password": "SuperSecurePass123!"
}
```

**Response (`201 Created`):**
```json
{
  "user": {
    "id": 1,
    "name": "Dr. Alex Mercer",
    "email": "alex.mercer@healthcare.org",
    "date_joined": "2026-10-28T09:00:00Z"
  },
  "access": "eyJhbGciOi...",
  "refresh": "eyJhbGciOi..."
}
```

### 2. Login User
**Request:** `POST /api/auth/login/`
```json
{
  "email": "alex.mercer@healthcare.org",
  "password": "SuperSecurePass123!"
}
```

**Response (`200 OK`):**
```json
{
  "access": "eyJhbGciOi...",
  "refresh": "eyJhbGciOi..."
}
```

---

## API Endpoints

| Category | Method | Endpoint | Description |
| :--- | :--- | :--- | :--- |
| **Auth** | `POST` | `/api/auth/register/` | Register new user with name, email, password |
| **Auth** | `POST` | `/api/auth/login/` | Authenticate user; returns access and refresh JWT |
| **Auth** | `POST` | `/api/auth/token/refresh/` | Refresh expired access token |
| **Patients** | `POST` | `/api/patients/` | Add patient (assigned to authenticated user) |
| **Patients** | `GET` | `/api/patients/` | List all patients created by authenticated user |
| **Patients** | `GET` | `/api/patients/<id>/` | Get details of owned patient (`404` if unowned) |
| **Patients** | `PUT` | `/api/patients/<id>/` | Update owned patient details (`404` if unowned) |
| **Patients** | `DELETE`| `/api/patients/<id>/` | Delete owned patient record (`204`, `404` if unowned) |
| **Doctors** | `POST` | `/api/doctors/` | Add doctor (assigned to authenticated user) |
| **Doctors** | `GET` | `/api/doctors/` | Retrieve all doctors |
| **Doctors** | `GET` | `/api/doctors/<id>/` | Get details of owned doctor (`404` if unowned) |
| **Doctors** | `PUT` | `/api/doctors/<id>/` | Update owned doctor details (`404` if unowned) |
| **Doctors** | `DELETE`| `/api/doctors/<id>/` | Delete owned doctor record (`204`, `404` if unowned) |
| **Mappings** | `POST` | `/api/mappings/` | Assign doctor to patient (`patient_id`, `doctor_id`) |
| **Mappings** | `GET` | `/api/mappings/` | List mappings with nested patient & doctor details |
| **Mappings** | `GET` | `/api/mappings/<patient_id>/` | Get all doctors assigned to owned patient |
| **Mappings** | `DELETE`| `/api/mappings/<id>/` | Remove doctor assignment by mapping ID (`204`) |

---

## Data Safety & Access Rules

- **Ownership Isolation:** Users manage only their own patients, mappings, and created doctor records.
- **Privacy Preservation:** Cross-user detail, update, delete, or mapping queries return `404 Not Found` (not `403`) to avoid leaking whether another user's record exists.
- **Mapping Constraints:** A user may only map their own patient to their own doctor. Duplicate patient-doctor assignments are rejected with `400 Bad Request`.
- **Validation:** Enforces email formats, non-empty fields, and past dates for `date_of_birth`.

---

## Postman Collection

The file [`healthcare_api.postman_collection.json`](./healthcare_api.postman_collection.json) is included in the project root:
1. Open Postman and click **Import**.
2. Select `healthcare_api.postman_collection.json`.
3. Running **Register User** or **Login User** automatically sets the collection's `access_token` and `refresh_token` variables for subsequent requests.
