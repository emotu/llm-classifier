# Business Activity Classifier API

An intelligent API service that uses Large Language Models to classify businesses according to the European NACE Rev. 2 statistical classification system.

## Features

- Automated business classification using LLMs
- Company information extraction from websites
- Policy document generation
- Asynchronous background processing
- Vector similarity search for accurate classifications
- Email notifications

## Tech Stack

- **Framework**: FastAPI
- **Database**: PostgreSQL with asyncpg
- **LLM Providers**: 
  - OpenAI
  - Google Vertex AI
- **Key Libraries**:
  - Pydantic for data validation
  - SQLAlchemy for ORM
  - LangChain for LLM orchestration
  - Rich for CLI formatting
  - Typer for CLI commands

## Project Structure

### Core Components

- `/api` - FastAPI routes and endpoints
- `/models` - Database models and Pydantic schemas
- `/services` - Business logic and LLM integration
- `/tasks` - Background job processors
- `/utils` - Helper functions and utilities

### Key Features Explained

- **Company Classification**: Utilizes LLMs to classify companies into NACE Rev. 2 categories.
- **Policy Generation**: Generates ISO-compliant policy documents for companies.
- **Background Processing**: Asynchronous tasks for policy generation and email notifications.
- **Vector Search**: Efficient similarity search for accurate classifications.
- **Email Notifications**: Sends policy documents via email to company representatives.

## Requirements

### System Requirements
- Python 3.13+
- PostgreSQL 15+
- Google Cloud SDK (for GCP features)
- Node.js 18+ (for frontend development)

### Python Dependencies
- fastapi>=0.104.1
- pydantic>=2.5.2
- sqlalchemy>=2.0.23
- asyncpg>=0.29.0
- langchain>=0.0.350
- openai>=1.3.7
- google-cloud-aiplatform>=1.36.4
- jinja2>=3.1.2
- python-multipart>=0.0.6
- rich>=13.7.0
- typer>=0.9.0
- uvicorn>=0.24.0
- weasyprint>=60.1
- resend>=0.6.0

### Development Dependencies
- black>=23.11.0
- isort>=5.12.0
- mypy>=1.7.1
- pytest>=7.4.3
- pytest-asyncio>=0.21.1
- pytest-cov>=4.1.0
- ruff>=0.1.6

### Infrastructure Requirements
- Docker and Docker Compose for containerization
- Google Cloud Platform account for:
  - Cloud SQL (PostgreSQL)
  - Cloud Storage
  - Vertex AI (optional)
- OpenAI API key (if using OpenAI)
- Resend API key for email functionality


### Getting Started

1. Clone the repository
2. Install dependencies with `uv sync`
3. Set up your environment variables (see `app/config.py` for reference)
4. Run the application with `uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4`

### Configuration

- **Environment Variables**: Set in `.env.local` or `.env`
- **Database**: Configured in `app/config.py`
- **LLM Providers**: Configured in `app/config.py`
- **Email**: Configured in `app/config.py`
- **GCP**: Configured in `app/config.py`

