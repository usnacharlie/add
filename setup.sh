#!/bin/bash

# Member Registry System - Initial Setup Script

echo "========================================="
echo "Member Registry System - Initial Setup"
echo "========================================="

# Check Python version
echo "Checking Python version..."
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
REQUIRED_VERSION="3.11"

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then 
    echo "ERROR: Python $REQUIRED_VERSION or higher is required (found $PYTHON_VERSION)"
    exit 1
fi
echo "✓ Python version: $PYTHON_VERSION"

# Check PostgreSQL
echo "Checking PostgreSQL..."
if ! command -v psql &> /dev/null; then
    echo "ERROR: PostgreSQL is not installed"
    echo "Install with:"
    echo "  Ubuntu/Debian: sudo apt-get install postgresql postgresql-contrib"
    echo "  macOS: brew install postgresql@15"
    exit 1
fi
echo "✓ PostgreSQL installed"

# Check if PostgreSQL is running
if ! pg_isready -q 2>/dev/null; then
    echo "PostgreSQL is not running. Starting..."
    if command -v brew &> /dev/null; then
        brew services start postgresql@15
    else
        sudo service postgresql start
    fi
    sleep 3
fi

# Create database
echo "Creating database..."
if psql -lqt | cut -d \| -f 1 | grep -qw member_registry; then
    echo "Database 'member_registry' already exists"
else
    createdb member_registry
    echo "✓ Database created"
fi

# Create .env file
if [ -f .env ]; then
    echo ".env file already exists"
else
    echo "Creating .env file..."
    cp .env.example .env
    echo "✓ .env file created"
fi

# Install backend dependencies
echo "Installing backend dependencies..."
cd backend
if [ -d "venv" ]; then
    echo "Virtual environment already exists"
else
    python3 -m venv venv
    echo "✓ Virtual environment created"
fi

source venv/bin/activate
pip install -q --upgrade pip
pip install -q -r requirements.txt
echo "✓ Backend dependencies installed"
deactivate
cd ..

# Install frontend dependencies
echo "Installing frontend dependencies..."
cd frontend
if [ -d "venv" ]; then
    echo "Virtual environment already exists"
else
    python3 -m venv venv
    echo "✓ Virtual environment created"
fi

source venv/bin/activate
pip install -q --upgrade pip
pip install -q -r requirements.txt
echo "✓ Frontend dependencies installed"
deactivate
cd ..

# Initialize database
echo "Initializing database..."
cd backend
source venv/bin/activate
python3 -c "from backend.config.database import init_db; init_db()"
echo "✓ Database initialized"
deactivate
cd ..

# Create upload directories
echo "Creating upload directories..."
mkdir -p frontend/static/uploads/profiles
chmod 755 frontend/static/uploads
chmod 755 frontend/static/uploads/profiles
echo "✓ Upload directories created"

# Run migrations
echo "Running database migrations..."
cd backend
source venv/bin/activate

# Check if migrations are needed
if python3 -c "from sqlalchemy import inspect; from backend.config.database import engine; inspector = inspect(engine); print('voters_id' not in [c['name'] for c in inspector.get_columns('members')])" 2>/dev/null | grep -q "True"; then
    echo "Running voter_id migration..."
    cd ..
    python3 migrate_voters_id.py --auto
    cd backend
fi

deactivate
cd ..

# Seed sample data
echo "Would you like to seed sample data? (y/n)"
read -r response
if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
    if [ -d "database" ]; then
        cd database
        python3 seed_data.py
        echo "✓ Sample data seeded"
        cd ..
    else
        echo "⚠ Sample data seed script not found, skipping..."
    fi
fi

echo ""
echo "========================================="
echo "✓ Setup Complete!"
echo "========================================="
echo ""
echo "To start the application:"
echo "  ./start.sh"
echo ""
echo "To stop the application:"
echo "  ./stop.sh"
echo ""
echo "========================================="
