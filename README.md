# The Bridge - Lead Generation SaaS

A deterministic lead generation pipeline with a modern SaaS wrapper. Scrape Google Maps, enrich leads with website data, and generate personalized outreach templates.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      FRONTEND (Next.js)                      │
│                    localhost:3000                            │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      BACKEND (FastAPI)                       │
│                    localhost:8000                            │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐        │
│  │ Start   │  │  Get    │  │  List   │  │Download │        │
│  │ Job API │  │ Job API │  │Jobs API │  │  API    │        │
│  └────┬────┘  └─────────┘  └─────────┘  └─────────┘        │
│       │                                                      │
│       ▼                                                      │
│  ┌─────────────────────────────────────────────────────┐    │
│  │              BackgroundTasks                         │    │
│  │  Runs Python Engine asynchronously                   │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
                              │
          ┌───────────────────┼───────────────────┐
          ▼                   ▼                   ▼
    ┌──────────┐        ┌──────────┐        ┌──────────┐
    │  MongoDB │        │  Python  │        │  Exports │
    │   Jobs   │        │  Engine  │        │  (CSV)   │
    └──────────┘        └──────────┘        └──────────┘
```

## Python Engine Pipeline

```
Step 1: Search (Apify)     Step 2: Enrich         Step 3: Template      Step 4: Validate
┌─────────────────┐       ┌─────────────────┐    ┌─────────────────┐   ┌─────────────────┐
│  Google Maps    │──────▶│ Website Scrape  │───▶│ Pain Point Map  │──▶│ Pydantic Valid  │
│  nwua9Gu5YrADL  │       │ BeautifulSoup   │    │ No LLM - Pure   │   │ Deduplication   │
│                 │       │ Keyword Regex   │    │ Hash Map Logic  │   │                 │
└─────────────────┘       └─────────────────┘    └─────────────────┘   └─────────────────┘
      stage1.csv              stage2.csv            stage3.csv           final_leads.csv
```

## Quick Start

### Prerequisites
- Python 3.10+
- Node.js 18+
- MongoDB (or Docker)

### 1. Start MongoDB

```bash
# Using Docker
docker run -d -p 27017:27017 --name mongodb mongo:7

# Or use local MongoDB
```

### 2. Run Backend

```bash
cd backend
pip install -r requirements.txt
cd ../engine
pip install -r requirements.txt
cd ../backend
uvicorn app.main:app --reload
```

### 3. Run Frontend

```bash
cd frontend
npm install
npm run dev
```

### 4. Open Dashboard

Navigate to http://localhost:3000

## Docker Compose (Full Stack)

```bash
# Set your Apify token
export APIFY_API_TOKEN=your_token_here

# Start all services
docker-compose up --build
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/start-job` | Start a new lead generation job |
| GET | `/api/job/{id}` | Get job status and details |
| GET | `/api/jobs` | List all jobs |
| GET | `/api/download/{id}` | Download CSV for completed job |
| GET | `/api/health` | Health check |

## Environment Variables

### Backend (.env)
```
MONGODB_URL=mongodb://localhost:27017
DATABASE_NAME=thebridge
APIFY_API_TOKEN=your_apify_token
ENGINE_PATH=../engine
```

### Frontend (.env.local)
```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Tech Stack

- **Frontend**: Next.js 14, TypeScript, Tailwind CSS
- **Backend**: FastAPI, Pydantic v2, Motor (async MongoDB)
- **Database**: MongoDB
- **Scraping**: Apify Client, BeautifulSoup, Requests
- **Validation**: Pydantic with strict typing

## Philosophy

- **Zero Hallucination**: No LLMs in the execution pipeline
- **Fail-Fast**: Quality gates at every stage
- **File-Based State**: CSV files for intermediate data
- **Deterministic**: Same input = same output, always
