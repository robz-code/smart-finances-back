# Smart Finances

A FastAPI application for smart finances management.

## Features
- User, account, transaction, and tag management
- JWT authentication
- PostgreSQL/SQLite support
- Supabase integration

## Requirements
- Python 3.10+
- pip (Python package manager)
- (Optional) PostgreSQL database

## Setup Instructions

### 1. Clone the repository
```bash
git clone <repo-url>
cd smart-finances
```

### 2. Create a virtual environment
#### Mac/Linux
```bash
python3 -m venv venv
source venv/bin/activate
```
#### Windows
```cmd
python -m venv venv
venv\Scripts\activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure environment variables
Create a `.env` file in the root directory. Example:
```
PROJECT_NAME=Smart Finances
API_V1_STR=/api/v1
DATABASE_URL=sqlite:///./smart_finances.db
SUPABASE_URL=<your-supabase-url>
SUPABASE_KEY=<your-supabase-key>
JWT_SECRET_KEY=<your-jwt-secret>
BACKEND_CORS_ORIGINS=["*"]
SECRET_KEY=<your-secret-key>
```

### 5. Initialize the database 
> Not necessary if using Supabase
```bash
python create_db.py
```

### 6. Run the application
#### Mac/Linux
```bash
uvicorn app:app --reload
```
#### Windows
```cmd
uvicorn app:app --reload
```

The API will be available at `http://127.0.0.1:8000`.

## API Documentation
- Swagger UI: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- ReDoc: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

## Notes
- For PostgreSQL, update `DATABASE_URL` in `.env` accordingly (e.g., `postgresql://user:password@localhost/dbname`).
- Ensure your Supabase credentials are correct for authentication features.

## License
MIT 