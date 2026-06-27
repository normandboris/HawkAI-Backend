# HawkAI — Project Context for Claude Code

## What this project is
HawkAI is an AI-powered financial aid chatbot for Hunter College CUNY students.
Students type any financial aid question in plain English and get an accurate,
source-grounded answer pulled from official Hunter College financial aid webpages.
The bot never answers from general AI knowledge — only from scraped Hunter data.

This is a CSCI 49900 Senior Capstone project at Hunter College.

---

## The one sentence that defines everything
"A student types a financial aid question → Flask searches Supabase for relevant
scraped Hunter data → sends that data + question to Claude API → Claude writes a
natural answer citing the source URL → student sees the answer."

---

## Tech stack

| Layer | Tool | Notes |
|---|---|---|
| Frontend | React | Deployed on Vercel |
| Backend / API | Flask (Python) | Deployed on Render |
| Database + Auth | Supabase + pgvector | Handles everything — DB, auth, vector search |
| AI model | Claude API (claude-sonnet-4-6) | Temperature 0.0 — no creative variance |
| Embeddings | Voyage AI (voyage-3-lite) | Converts text chunks to vectors for semantic search |
| Scraping | Python + BeautifulSoup | Scrapes Hunter financial aid pages |
| Hosting | GitHub Pages (React) + Render (Flask) | Both free tiers |

---

## Folder structure

```
HawkAI-Backend/          ← this repo (backend + scraper)
├── CLAUDE.md            ← this file
├── app.py               ← main Flask app entry point
├── routes/
│   ├── chat.py          ← /chat route — RAG pipeline lives here
│   ├── auth.py          ← /auth routes — admin login via Supabase Auth
│   └── admin.py         ← /admin routes — knowledge base CRUD, feedback viewer
├── rag/
│   ├── search.py        ← searches Supabase knowledge_base using hybrid search
│   ├── embeddings.py    ← calls Voyage AI to convert text to vectors
│   └── prompt.py        ← builds the Claude system prompt with retrieved context
├── scraper/
│   ├── scrape_main.py   ← full scrape — runs twice per semester
│   ├── scrape_deadlines.py ← lightweight scrape — runs monthly for deadline updates
│   └── save_to_supabase.py ← inserts/upserts scraped chunks into Supabase
├── supabase_client.py   ← single Supabase client shared across the app
├── requirements.txt     ← all Python dependencies
└── .env                 ← API keys (never commit this file)
```

Frontend lives in a separate repo: HawkAI-Frontend (React)

---

## Supabase tables

### knowledge_base
Stores scraped Hunter financial aid content — the bot searches this before answering.
```sql
id          uuid primary key default gen_random_uuid()
category    text        -- 'deadlines', 'eligibility', 'process', 'faq'
question    text        -- the question or topic heading
answer      text        -- the scraped answer text (150-250 token chunks)
source_url  text        -- which Hunter page this came from
embedding   vector(1024) -- Voyage AI embedding of the answer text
last_updated timestamp default now()
```

### conversations
Stores every message in every chat session so the bot has memory.
```sql
id           uuid primary key default gen_random_uuid()
session_id   text        -- random ID generated when student opens the app
role         text        -- 'user' or 'assistant'
message      text        -- the actual message content
created_at   timestamp default now()
```

### feedback
Stores student thumbs up / down ratings on bot answers.
```sql
id              uuid primary key default gen_random_uuid()
session_id      text
question        text        -- what the student asked
answer          text        -- what the bot replied
rating          boolean     -- true = thumbs up, false = thumbs down
created_at      timestamp default now()
```

### offices
Stores Hunter office locations, hours, phone numbers.
```sql
id          uuid primary key default gen_random_uuid()
name        text        -- 'Financial Aid Office'
location    text        -- 'Room 241, North Building'
phone       text
hours       text
email       text
website     text
```

### Admin auth
Handled by Supabase Auth built-in system — NO separate table needed.
Admin accounts are created manually in Supabase dashboard under Authentication > Users.

---

## Pages we scrape

Full scrape twice per semester + monthly deadline-only scrape:

1. https://www.hunter.cuny.edu/students/financial-aid/ — main page, deadlines table, announcements
2. https://www.hunter.cuny.edu/students/financial-aid/faq — pre-built Q&A pairs
3. https://www.hunter.cuny.edu/students/financial-aid/eligibility — federal and state aid requirements
4. https://www.hunter.cuny.edu/students/financial-aid/types — TAP, FAFSA, loans, work-study

Chunking: 150-250 tokens per chunk, 25-token overlap between chunks.
Smaller chunks = more targeted retrieval for short discrete financial aid content.

---

## How RAG works in this project

1. Student sends a question via React → POST /chat
2. Flask calls Voyage AI to embed the question into a vector
3. Flask runs hybrid search on Supabase:
   - Cosine similarity search on the embedding column (semantic matching)
   - BM25 keyword search (exact matching for terms like TAP, FAFSA, SAP, Excelsior)
4. Flask retrieves the top 3-5 most relevant knowledge_base rows
5. Flask builds a prompt:
   ```
   System: You are HawkAI, Hunter College financial aid assistant.
   Answer ONLY from the provided context.
   Always cite the source_url at the end of your answer.
   If context is empty, say "I don't have that information."
   Temperature: 0.0

   Context: [retrieved knowledge_base rows]
   Question: [student's question]
   ```
6. Flask sends to Claude API (claude-sonnet-4-6, temperature 0.0)
7. Claude returns answer — Flask saves to conversations table
8. Flask returns answer to React → student sees it with source citation

---

## Flask routes

| Route | Method | What it does |
|---|---|---|
| /health | GET | Returns "HawkAI is running" — health check |
| /chat | POST | Main RAG endpoint — receives question, returns answer |
| /auth/login | POST | Verifies admin credentials via Supabase Auth |
| /auth/logout | POST | Logs out admin |
| /admin/knowledge | GET | Returns all knowledge_base entries |
| /admin/knowledge | POST | Adds a new entry |
| /admin/knowledge/<id> | PUT | Updates an entry |
| /admin/knowledge/<id> | DELETE | Deletes an entry |
| /admin/conversations | GET | Returns recent chat history |
| /admin/feedback | GET | Returns all feedback with ratings |

All /admin routes require a valid Supabase Auth token in the request header.

---

## Environment variables (.env file)

```
SUPABASE_URL=your_supabase_project_url
SUPABASE_KEY=your_supabase_anon_key
ANTHROPIC_API_KEY=your_claude_api_key
VOYAGE_API_KEY=your_voyage_ai_key
FLASK_ENV=development
```

NEVER commit the .env file. It is in .gitignore.

---

## Team roles

| Person | Role | Responsible for |
|---|---|---|
| You (student running Claude Code) | Team lead + full-stack | Coordination, any file that needs building |
| Mohammed | Backend | Flask routes, RAG pipeline logic, Claude API integration |
| Boris | AI & Scraping | BeautifulSoup scraper, Voyage AI embeddings, evaluation test set |
| Raymond | Frontend | React chat UI, admin panel pages, dark mode, responsive design |
| Mahdi | Database & DevOps | Supabase schema, pgvector setup, Render deployment |

Since you are using Claude Code to help build multiple parts, Claude Code
should be ready to work on ANY of these areas when asked.

---

## What is already decided (do not change these)

- AI model: claude-sonnet-4-6 at temperature 0.0 — non-negotiable for accuracy
- Database: Supabase only — no other database
- Embeddings: Voyage AI voyage-3-lite — already in the report
- Chunking: 150-250 tokens, 25-token overlap — already justified in report
- Search: hybrid BM25 + cosine similarity — already committed to in report
- Domain: Hunter College financial aid ONLY — not general campus info
- No student login — students use the app without an account
- Admin login: Supabase Auth email + password only — no Google/OAuth

---

## Evaluation plan (professor requirement)

75 test questions across 3 domains:
- 25 questions about deadlines and dates
- 25 questions about eligibility and requirements
- 25 questions about process and documentation

Each answer graded on:
- Faithfulness: is the answer grounded in retrieved content? (pass/fail)
- Answer relevance: does it answer the question? (1-3 scale)
- Source grounding: does it cite a Hunter source URL? (pass/fail)

Failed answers documented by failure type:
- Missing data (not in scraped content)
- Wrong retrieval (wrong chunk returned)
- Generation error (Claude misread the context)

---

## Current project status

Phase 1 — Setup (in progress)
- [ ] GitHub repo created
- [ ] Supabase project created with all 5 tables
- [ ] API keys obtained (Claude + Voyage AI)
- [ ] Folder structure set up

Phase 2 — Core build (not started)
- [ ] Flask /health and /chat routes working
- [ ] React chat UI built and connected to Flask
- [ ] Claude API connected to Flask
- [ ] Admin login page working

Phase 3 — RAG pipeline (not started)
- [ ] Scraper pulling Hunter financial aid pages into Supabase
- [ ] Voyage AI embeddings added to scraped chunks
- [ ] Hybrid search implemented in Flask
- [ ] Chat history saved to conversations table

Phase 4 — Admin panel and polish (not started)
- [ ] Admin panel pages (conversations, knowledge base editor, feedback viewer)
- [ ] Thumbs up/down feedback saving to Supabase
- [ ] Source citations showing in every answer
- [ ] Chat UI styled properly with dark mode

Phase 5 — Evaluation and demo (not started)
- [ ] 75-question test set run and graded
- [ ] Error analysis documented
- [ ] App deployed on Vercel + Render
- [ ] Final presentation updated with results

---

## Key dates

- 6/24 — Written proposal submitted
- 7/06 — Progress Presentation 1 (need: working chat UI + basic RAG)
- 7/20 — Progress Presentation 2 (need: full end-to-end demo)
- 8/05 — Student interviews (need: polished UI + evaluation done)
- 8/12 — Final presentation and delivery

---

## Notes for Claude Code

- Always use the Supabase client from supabase_client.py — never create a new one
- Always call Claude with temperature=0.0 — this is required for accuracy
- Always include source_url in every answer via the system prompt
- When the knowledge_base search returns empty, return "I don't have that information on the official Hunter website. Please contact the financial aid office at Room 241 North Building."
- Flask should never call Claude directly without first searching Supabase
- All admin routes must check for a valid Supabase Auth token before doing anything
- Use upsert not insert when saving scraped data — prevents duplicates on re-runs
- Python dependencies go in requirements.txt, never install globally without adding there
