# QTravix – QR-Assisted Local Bus Ticketing and Record Management System

## About the Project

QTravix is a web-based mini-project designed to simplify local bus ticketing and record management using QR codes. It provides separate access for administrators and conductors, helping manage bus information, bookings, and ticket validation.

## Features

- Admin registration and login
- Conductor registration and login
- Bus and route management
- QR code generation for bus ticket booking
- Ticket booking and fare calculation
- Digital ticket generation
- QR-based ticket validation
- Daily and monthly revenue reports
- Role-based access to dashboards

## Technologies Used

- Python
- Flask
- Flask-SQLAlchemy
- SQLite
- HTML and CSS
- JavaScript, where applicable
- QR code generation using Python

## Requirements

- Python 3
- pip
- A web browser

## Installation and Setup

### 1. Clone the repository

```bash
git clone YOUR_GITHUB_REPOSITORY_URL
cd QTravix
```

Replace `YOUR_GITHUB_REPOSITORY_URL` with the repository URL.

### 2. Create a virtual environment

```bash
python -m venv .venv
```

Activate it on Windows:

```powershell
.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Initialize and run the application

Run:

```bash
python app.py
```

The application creates its database tables and initializes sample data when appropriate.

Open the local address displayed by Flask in your browser.

If the database is empty, the application creates sample admin, conductor, and bus records.

## Database

QTravix uses SQLite to store application records. The local database file is excluded from the repository so that personal or development records are not published.

## Security Note

The application is intended as an academic project. Configure a secure secret key and disable Flask debug mode before deploying it publicly. Do not use demonstration credentials in a production environment.

## Project Status

Academic mini-project developed for learning and demonstration purposes.