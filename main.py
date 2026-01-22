import json
import os
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from psycopg_pool import AsyncConnectionPool
from google import genai

load_dotenv()

# Database configuration
DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", "5434")),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", "postgres"),
    "dbname": os.getenv("DB_NAME", "practice_db"),
}

# connection string
DATABASE_URL = f"postgresql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['dbname']}"

# Connection pool (initialized on startup)
pool: AsyncConnectionPool | None = None

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

gemini_client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None


class ParseRequest(BaseModel):
    text: str
    llm: str


class ParseResponse(BaseModel):
    name: str | None
    email: str | None
    phone: str | None
    found_in_database: bool
    company: str | None


# LLM extraction system prompt
EXTRACTION_SYSTEM_PROMPT = """Extract contact information from the given text.
Return a JSON object with these fields:
- name: The person's full name (string or null if not found)
- email: The email address (string or null if not found)
- phone: The phone number (string or null if not found)

Return ONLY the JSON object, no other text or markdown formatting."""


def parse_llm_response(response_text: str) -> dict:
    response_text = response_text.strip()
    
    # Clean up response - remove markdown code blocks if present
    if response_text.startswith("```"):
        lines = response_text.split("\n")
        # Remove first line (```json) and last line (```)
        lines = [l for l in lines if not l.startswith("```")]
        response_text = "\n".join(lines).strip()
    
    try:
        extracted = json.loads(response_text)
    except json.JSONDecodeError:
        # If JSON parsing fails, return nulls
        extracted = {"name": None, "email": None, "phone": None}
    
    return {
        "name": extracted.get("name"),
        "email": extracted.get("email"),
        "phone": extracted.get("phone"),
    }


async def extract_contact_with_gemini(text: str, model_name: str) -> dict:
    if not gemini_client:
        raise HTTPException(
            status_code=500,
            detail="Cannot reach Google Gemini"
        )
    
    prompt = f"{EXTRACTION_SYSTEM_PROMPT}\n\nText to extract from:\n{text}"
    
    response = gemini_client.models.generate_content(
        model=model_name,
        contents=prompt,
    )
    
    return parse_llm_response(response.text)


async def lookup_contact_in_database(name: str) -> dict | None:

    if not name or not pool:
        return None
    
    async with pool.connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                SELECT full_name, email, phone, company_name 
                FROM contact_directory 
                WHERE full_name ILIKE %s
                """,
                (name,)
            )
            row = await cur.fetchone()
            
            if row:
                return {
                    "full_name": row[0],
                    "email": row[1],
                    "phone": row[2],
                    "company_name": row[3],
                }
    
    return None


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Manage application lifespan - setup and teardown.
    global pool
    # Startup: Create connection pool
    pool = AsyncConnectionPool(conninfo=DATABASE_URL, min_size=1, max_size=10)
    await pool.open()
    yield
    # Shutdown: Close connection pool
    await pool.close()


app = FastAPI(
    title="Contact Information Parser",
    description="REST API for extracting contact information using LLM and validating against a database",
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/health")
async def health_check():
    # Health check endpoint.
    # Verifies the API is running and database is connected.
    try:
        async with pool.connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute("SELECT 1")
                await cur.fetchone()
        return {"status": "ok", "database": "connected"}
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail={"status": "error", "database": "disconnected", "error": str(e)},
        )


@app.post("/parse", response_model=ParseResponse)
async def parse_contact(request: ParseRequest):
    # Extract contact info using Gemini
    extracted = await extract_contact_with_gemini(request.text, request.llm)
    
    # Look up contact in database
    found_in_database = False
    company = None
    
    if extracted.get("name"):
        db_contact = await lookup_contact_in_database(extracted["name"])
        if db_contact:
            found_in_database = True
            company = db_contact.get("company_name")
    
    return ParseResponse(
        name=extracted.get("name"),
        email=extracted.get("email"),
        phone=extracted.get("phone"),
        found_in_database=found_in_database,
        company=company,
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
