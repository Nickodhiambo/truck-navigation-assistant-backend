# Truck Navigation Web Service Backend

## Overview
The backend of a Truck Navigation Web Service built using Django. It processes route data, interacts with external APIs for location and routing, and generates detailed PDF log sheets for drivers. The backend is responsible for:

- Geocoding and reverse geocoding using the Geopy library.
- Fetching routes and stop details via the OpenStreetMap API.
- Generating PDF log sheets using PyPDF2 and ReportLab.

## Features
- REST API endpoints for route planning and PDF generation.
- Integration with Geopy and OpenStreetMap API.
- Comprehensive PDF log sheet generation.
- REST API endpoints that fetch hours of service from database.

## Requirements
To set up and run the backend, ensure you have the following:

- Python 3.8 or higher

## Installation
1. Clone the repository:
   ```bash
   git clone https://github.com/Nickodhiambo/truck-navigation-assistant-backend.git
   ```
2. Change into project directory:
   ```bash
   cd truck-navigation-assistant-backend
3. Set up a virtual environment:
   ```bash
   python -m venv env
   source env/bin/activate  # On Windows: env\Scripts\activate
   ```
4. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Environment Variables
Create a `.env` file in the root directory with the following keys:

- `SECRET_KEY`: Django's secret key.
- `DEBUG`: Set to `True` for development, `False` for production.
- `DATABASE_URL`: Connection URL for the database.

Example:
```
SECRET_KEY=your_secret_key
DEBUG=True
DATABASE_URL=postgres://user:password@localhost:5432/dbname
```

## Running the Application
1. Apply database migrations:
   ```bash
   python manage.py migrate
   ```
2. Start the development server:
   ```bash
   python manage.py runserver
   ```
3. The API will be available at `http://localhost:8000`.

## API Endpoints
# Route planning
- **Route Planning**: `/api/route/plan/`
  - Method: POST
  - Description: Accepts input data (current location, pickup, dropoff, hours of service) and returns route details including stops.
- **Hours of Service** `/api/hours-of-service/current/`
  - Method: GET
  - Description: Returns current driving, duty and cycle hours for a given day for a driver.
- **Recent Trips** `trips/recent/`
  - Method: GET
  - Description: Gets recent trips for a given driver.
- **PDF Generation**: `api/driver-logs/pdf/`
  - Method: POST
  - Description: Generates and returns a PDF log sheet for the planned route.
 
# Authentication
- **Driver Account Registration**: `accounts/register/driver/`
  - Method: POST
  - Inputs: `First Name`, `Last Name`, `Email`, `Driver Number`, `Phone Number`, `Password`
  - Description: Creates a driver account
 
- **Login** `accounts/login/`
  - Method: POST
  - Inputs: `Email`, `Password`
  - Description: Login endpoint

- **User Info** `accounts/user/`
- Method: GET
- Description: Gets a user and their complete profile from the database

## Libraries Used
- `django`: Web framework for building the backend.
- `djangorestframework`: To build REST APIs
- `geopy`: For geocoding and reverse geocoding.
- `requests`: For making API calls to OpenStreetMap.
- `PyPDF2` and `ReportLab`: For PDF processing.

## Contributing
1. Fork the repository.
2. Create a new branch:
   ```bash
   git checkout -b feature-name
   ```
3. Make your changes and commit them:
   ```bash
   git commit -m "Add feature-name"
   ```
4. Push your changes:
   ```bash
   git push origin feature-name
   ```
5. Open a pull request.

## License
This project is licensed under the MIT License. See the LICENSE file for details.

## Contact
For questions or support, contact nodhiambo01@gmail.com.

