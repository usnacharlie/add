# Member Registry System

A comprehensive member registration management system with FastAPI backend and Flask frontend for managing member information organized by Province, District, and Ward.

## Features

- **Registration Forms**: Submit and manage member registration forms with up to 50 members per form
- **Member Management**: Full CRUD operations for member records
- **Location Hierarchy**: Organize data by Province → District → Ward
- **Search & Filter**: Search members by name, NRC, or Voter's ID
- **RESTful API**: Complete REST API with FastAPI
- **Web Interface**: User-friendly Flask-based web interface
- **Database**: PostgreSQL for reliable data storage
- **Modular Architecture**: Clean separation of concerns for easy maintenance

## Technology Stack

### Backend
- **FastAPI**: Modern, fast web framework for building APIs
- **SQLAlchemy**: SQL toolkit and ORM
- **PostgreSQL**: Robust relational database
- **Alembic**: Database migration tool
- **Pydantic**: Data validation using Python type annotations

### Frontend
- **Flask**: Lightweight WSGI web application framework
- **Jinja2**: Template engine for Python
- **HTML/CSS/JavaScript**: Modern web technologies
- **Responsive Design**: Mobile-friendly interface

## Project Structure

```
member/
├── backend/              # FastAPI backend application
│   ├── config/          # Configuration and database setup
│   ├── models/          # SQLAlchemy database models
│   ├── schemas/         # Pydantic schemas for validation
│   ├── routes/          # API route handlers
│   ├── services/        # Business logic layer
│   ├── main.py          # FastAPI application entry point
│   ├── requirements.txt # Python dependencies
│   └── Dockerfile       # Docker configuration
├── frontend/            # Flask frontend application
│   ├── templates/       # Jinja2 HTML templates
│   ├── static/          # CSS, JavaScript, images
│   ├── routes/          # Flask route handlers
│   ├── app.py           # Flask application entry point
│   ├── requirements.txt # Python dependencies
│   └── Dockerfile       # Docker configuration
├── database/            # Database related files
│   ├── migrations/      # Alembic migration scripts
│   └── seed_data.py     # Sample data seeding script
├── docker-compose.yml   # Docker Compose configuration
├── .env.example         # Environment variables template
└── README.md            # This file
```

## Getting Started

### Prerequisites

- Python 3.11+
- PostgreSQL 15+
- Docker & Docker Compose (optional, for containerized deployment)

### Installation

#### Option 1: Manual Setup

1. **Clone the repository**
   ```bash
   cd /opt/test/ffan/member
   ```

2. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Set up PostgreSQL database**
   ```bash
   createdb member_registry
   ```

4. **Install backend dependencies**
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

5. **Install frontend dependencies**
   ```bash
   cd ../frontend
   pip install -r requirements.txt
   ```

6. **Run database migrations**
   ```bash
   cd ../database/migrations
   alembic upgrade head
   ```

7. **Seed sample data (optional)**
   ```bash
   cd ..
   python seed_data.py
   ```

8. **Start the backend server** (Port 9500)
   ```bash
   cd ../backend
   python main.py
   ```

9. **Start the frontend server** (Port 9100) in a new terminal
   ```bash
   cd ../frontend
   python app.py
   ```

10. **Access the application**
    - Frontend: http://localhost:9100
    - Backend API: http://localhost:9500
    - API Documentation: http://localhost:9500/docs

#### Option 2: Docker Setup

1. **Set up environment variables**
   ```bash
   cp .env.example .env
   ```

2. **Build and start containers**
   ```bash
   docker-compose up -d
   ```

3. **Run migrations**
   ```bash
   docker-compose exec backend alembic -c database/migrations/alembic.ini upgrade head
   ```

4. **Seed sample data (optional)**
   ```bash
   docker-compose exec backend python database/seed_data.py
   ```

5. **Access the application**
   - Frontend: http://localhost:9100
   - Backend API: http://localhost:9500
   - API Documentation: http://localhost:9500/docs

## API Endpoints

### Provinces
- `GET /api/v1/provinces/` - List all provinces
- `POST /api/v1/provinces/` - Create a province
- `GET /api/v1/provinces/{id}` - Get province by ID
- `DELETE /api/v1/provinces/{id}` - Delete a province

### Districts
- `GET /api/v1/districts/` - List all districts
- `POST /api/v1/districts/` - Create a district
- `GET /api/v1/districts/{id}` - Get district by ID
- `GET /api/v1/districts/province/{province_id}` - Get districts by province
- `DELETE /api/v1/districts/{id}` - Delete a district

### Wards
- `GET /api/v1/wards/` - List all wards
- `POST /api/v1/wards/` - Create a ward
- `GET /api/v1/wards/{id}` - Get ward by ID
- `GET /api/v1/wards/district/{district_id}` - Get wards by district
- `DELETE /api/v1/wards/{id}` - Delete a ward

### Members
- `GET /api/v1/members/` - List all members
- `POST /api/v1/members/` - Create a member
- `GET /api/v1/members/{id}` - Get member by ID
- `PUT /api/v1/members/{id}` - Update a member
- `DELETE /api/v1/members/{id}` - Delete a member
- `GET /api/v1/members/nrc/{nrc}` - Get member by NRC
- `GET /api/v1/members/voters-id/{voters_id}` - Get member by Voter's ID
- `GET /api/v1/members/ward/{ward_id}` - Get members by ward
- `GET /api/v1/members/?name={search}` - Search members by name

### Forms
- `GET /api/v1/forms/` - List all forms
- `POST /api/v1/forms/` - Create form metadata
- `POST /api/v1/forms/submit` - Submit complete form with members
- `GET /api/v1/forms/{id}` - Get form by ID
- `GET /api/v1/forms/ward/{ward_id}` - Get forms by ward
- `DELETE /api/v1/forms/{id}` - Delete a form

## Database Schema

### Tables

1. **provinces**
   - id (Primary Key)
   - name (Unique)
   - created_at
   - updated_at

2. **districts**
   - id (Primary Key)
   - name
   - province_id (Foreign Key → provinces.id)
   - created_at
   - updated_at

3. **wards**
   - id (Primary Key)
   - name
   - district_id (Foreign Key → districts.id)
   - created_at
   - updated_at

4. **form_metadata**
   - id (Primary Key)
   - province_id (Foreign Key → provinces.id)
   - district_id (Foreign Key → districts.id)
   - ward_id (Foreign Key → wards.id)
   - prepared_by
   - sign
   - contact
   - submission_date
   - created_at
   - updated_at

5. **members**
   - id (Primary Key)
   - name
   - gender (Enum: M, F, Other)
   - age
   - nrc (National Registration Card)
   - voters_id
   - contact
   - ward_id (Foreign Key → wards.id)
   - form_metadata_id (Foreign Key → form_metadata.id)
   - created_at
   - updated_at

## Usage Guide

### Submitting a Registration Form

1. Navigate to "Forms" → "New Form"
2. Fill in the form metadata:
   - Select Province, District, and Ward
   - Enter "Prepared By" name
   - Add signature (optional)
   - Enter contact information
   - Set submission date
3. Add member information:
   - Click "Add Member" to add more members (up to 50)
   - Fill in member details: Name, Gender, Age, NRC, Voter's ID, Contact
4. Click "Submit Form" to save

### Searching for Members

1. Navigate to "Members"
2. Use the search box to search by name
3. Click "View" to see full member details
4. Click "Edit" to update member information

### Managing Locations

1. Navigate to "Locations"
2. View and manage Provinces, Districts, and Wards
3. Add new locations as needed

## Development

### Running Tests
```bash
# Backend tests (to be implemented)
cd backend
pytest

# Frontend tests (to be implemented)
cd frontend
pytest
```

### Creating Database Migrations
```bash
cd database/migrations
alembic revision --autogenerate -m "Description of changes"
alembic upgrade head
```

### Code Style
- Follow PEP 8 for Python code
- Use type hints where appropriate
- Write docstrings for functions and classes

## Configuration

### Environment Variables

- `DATABASE_URL`: PostgreSQL connection string
- `API_BASE_URL`: Backend API URL for frontend
- `SECRET_KEY`: Flask secret key for sessions
- `FLASK_ENV`: Flask environment (development/production)

## Troubleshooting

### Database Connection Issues
- Ensure PostgreSQL is running
- Check DATABASE_URL in .env file
- Verify database exists: `psql -l`

### Port Already in Use
- Backend (9500): `lsof -ti:9500 | xargs kill -9`
- Frontend (9100): `lsof -ti:9100 | xargs kill -9`

### Migration Issues
- Reset migrations: Drop database and recreate
- Check alembic.ini configuration
- Ensure models are imported in env.py

## Security Considerations

- Change SECRET_KEY in production
- Use environment-specific database credentials
- Enable HTTPS in production
- Implement authentication/authorization (to be added)
- Sanitize user inputs
- Use prepared statements (SQLAlchemy handles this)

## Future Enhancements

- [ ] User authentication and authorization
- [ ] Role-based access control
- [ ] Export data to CSV/Excel
- [ ] Import data from spreadsheets
- [ ] Advanced filtering and reporting
- [ ] Audit logs
- [ ] Email notifications
- [ ] Mobile application
- [ ] Offline mode support
- [ ] Data analytics dashboard

## License

This project is proprietary software. All rights reserved.

## Support

For issues, questions, or contributions, please contact the development team.

## Acknowledgments

Built with modern Python web frameworks to provide a robust member registration system.
