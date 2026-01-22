# Contact Information Parser

## Description
A FastAPI-based service that extracts contact details (name, email, and phone number) from natural language text using the Google Gemini LLM and validates the extracted name against a PostgreSQL database to determine if the contact exists and retrieve their company name.

## Startup Guide

### 1. Prerequisites
- Docker and Docker Compose
- Python 3.10+
- Google Gemini API Key

### 2. Environment Setup
Create a `.env` file in the root directory:
```env
GEMINI_API_KEY=your_api_key_here
DB_HOST=localhost
DB_PORT=5434
DB_USER=postgres
DB_PASSWORD=postgres
DB_NAME=practice_db
```

### 3. Installation
```bash
# Install dependencies
pip install -r requirements.txt
```

### 4. Database Setup
Start the PostgreSQL database using Docker:
```bash
docker-compose up -d
```

### 5. Running the Application
```bash
python main.py
```
The API will be available at `http://localhost:8000`.

### 6. Testing
Run the automated checker to verify the implementation:
```bash
python checker/checker.py
```