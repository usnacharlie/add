# Quick Start Guide

Get the Member Registry System up and running in minutes!

## Prerequisites Check

```bash
# Check Python version (need 3.11+)
python3 --version

# Check PostgreSQL (need 15+)
psql --version

# Check Docker (optional)
docker --version
docker-compose --version
```

## Quick Setup (5 minutes)

### Step 1: Database Setup
```bash
# Create PostgreSQL database
createdb member_registry

# Or using psql
psql -U postgres
CREATE DATABASE member_registry;
\q
```

### Step 2: Environment Configuration
```bash
# Copy environment template
cp .env.example .env

# Edit if needed (optional - defaults work for local development)
nano .env
```

### Step 3: Install Dependencies
```bash
# Install backend dependencies
cd backend
pip install -r requirements.txt
cd ..

# Install frontend dependencies
cd frontend
pip install -r requirements.txt
cd ..
```

### Step 4: Database Initialization
```bash
# Initialize database schema
cd backend
python -c "from backend.config.database import init_db; init_db()"
cd ..

# Seed sample data (optional but recommended)
cd database
python seed_data.py
cd ..
```

### Step 5: Start the Applications

**Terminal 1 - Backend:**
```bash
cd backend
python main.py
```

**Terminal 2 - Frontend:**
```bash
cd frontend
python app.py
```

## Access the Application

- **Web Interface**: http://localhost:9100
- **API Documentation**: http://localhost:9500/docs
- **API Base URL**: http://localhost:9500/api/v1

## First Steps

1. **Explore the Dashboard**: Navigate to http://localhost:9100
2. **View Sample Data**: Click on "Locations" to see provinces, districts, and wards
3. **Create a Form**: Click "New Registration Form" to submit member data
4. **Search Members**: Use the Members section to search and view registered members

## Docker Quick Start (Alternative)

If you prefer Docker:

```bash
# Start all services
docker-compose up -d

# Initialize database
docker-compose exec backend python -c "from backend.config.database import init_db; init_db()"

# Seed sample data
docker-compose exec backend python database/seed_data.py

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

## Common Tasks

### Add a Province
```bash
curl -X POST http://localhost:9500/api/v1/provinces/ \
  -H "Content-Type: application/json" \
  -d '{"name": "New Province"}'
```

### Add a District
```bash
curl -X POST http://localhost:9500/api/v1/districts/ \
  -H "Content-Type: application/json" \
  -d '{"name": "New District", "province_id": 1}'
```

### Search Members
```bash
curl http://localhost:9500/api/v1/members/?name=John
```

## Troubleshooting

### "Database does not exist"
```bash
createdb member_registry
```

### "Port already in use"
```bash
# Kill process on port 9500
lsof -ti:9500 | xargs kill -9

# Kill process on port 9100
lsof -ti:9100 | xargs kill -9
```

### "Module not found"
```bash
# Ensure you're in the right directory and have activated virtual environment
cd backend  # or frontend
pip install -r requirements.txt
```

### Database Connection Error
```bash
# Check PostgreSQL is running
pg_isready

# Start PostgreSQL if needed (Ubuntu/Debian)
sudo service postgresql start

# macOS
brew services start postgresql@15
```

## Next Steps

- Read the full [README.md](README.md) for detailed documentation
- Explore the API at http://localhost:9500/docs
- Customize the system for your needs
- Add authentication (planned feature)

## Getting Help

- Check logs in terminal windows
- Visit API docs: http://localhost:9500/docs
- Review database schema in README.md
- Contact the development team

Happy registering! 🎉
