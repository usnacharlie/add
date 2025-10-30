# Project Overview: Member Registry System

This document provides a high-level overview of the Member Registry System project.

## 1. Purpose

The project is a comprehensive member registration and management system designed to handle member information organized by a geographical hierarchy of Province, District, and Ward. It appears to be tailored for a Zambian context, given the presence of files related to Zambian geography and USSD integration.

The system provides a full suite of features for managing member data, from submission of registration forms to individual record management.

## 2. Key Features

*   **Member Management**: Full CRUD (Create, Read, Update, Delete) operations for member records.
*   **Geographical Hierarchy**: Organizes member data by Province, District, and Ward.
*   **Bulk Registration**: Supports submitting and managing registration forms that can contain multiple members.
*   **Search and Filtering**: Allows searching for members by various identifiers like name, National Registration Card (NRC), or Voter's ID.
*   **USSD Integration**: Contains services related to USSD, suggesting functionality for mobile users to interact with the system via USSD codes.
*   **API and Web Interface**: The system is split into a backend RESTful API and a user-facing web interface.

## 3. Technology Stack

The project is built with a modern web stack, separating the backend API from the frontend user interface.

*   **Backend**:
    *   **Framework**: FastAPI (a modern, high-performance Python web framework).
    *   **Database**: PostgreSQL.
    *   **ORM**: SQLAlchemy with Alembic for database migrations.
    *   **Data Validation**: Pydantic.

*   **Frontend**:
    *   **Framework**: Flask (a lightweight Python web framework).
    *   **Templating**: Jinja2.
    *   **Standard Web Technologies**: HTML, CSS, JavaScript.

*   **Deployment**:
    *   The project is containerized using Docker, with a `docker-compose.yml` file for orchestrating the different services (backend, frontend, database).

## 4. Architecture

The application follows a standard client-server architecture:

*   **`backend/`**: Contains the FastAPI application that serves the RESTful API. This is the core of the application, handling all business logic, database interactions, and data validation.
*   **`frontend/`**: Contains the Flask application that provides the user-facing web interface. It communicates with the backend API to retrieve and display data.
*   **`database/`**: Holds database-related scripts, including migrations and data seeding scripts.
