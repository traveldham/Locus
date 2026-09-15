Read ME First - Reviewer (Important)

These are my personal written Note-work why, how and what is the idea and approached i used in building this . 6 Answers i have written that covers all your answers.  As i refined the English using chatgpt but context and words are my own don’t assume this as AI generated.

How I approached the problem
----------------------------

My starting point was not the UI or the AI layer. I first tried to understand what the supplied data represents and what problem a business with many locations would actually have.

The dataset closely resembles the information available around a Google Business Profile: profile information, reviews and replies, performance, search terms, bookings, content and ranking data, with additional intelligence such as tracked keywords and competitors.

A business can already use Google’s tools to manage much of its profile. The gap I saw was **decision-making**.

A business owner managing 5, 50 or 500 locations may have access to all this data but still not know:

*   Is this location actually performing well?
    
*   What is wrong with it?
    
*   What deserves attention first?
    
*   Why is visibility or customer activity weak?
    
*   What should I change?
    
*   If I make those changes, what part of the profile am I improving?
    

That led me to think of the prototype as an **intelligence layer above profile management**, rather than another dashboard that only displays metrics.

The longer-term product direction I explored is an end-to-end platform where a user could connect their Google account, import the Business Profiles they manage, manage those profiles, combine Google data with additional sources such as competitor and keyword data, audit every location, receive recommendations and eventually implement approved changes from the same product.

For this assignment, however, the core of that direction is the **audit and recommendation engine**.

**Decision and recommendation design**
--------------------------------------

I divided location health into six areas:

**Category**

**Weight**

**Question**

Local visibility

25%

Does the location appear when customers search, and how does it compare with competitors?

Profile completeness

20%

Is the listing complete, correct and useful?

Reputation

20%

What are customers saying, and is the business responding?

Operations

15%

Are appointment requests successfully becoming visits?

Performance

10%

Are impressions and customer actions holding up over time?

Content

10%

Is the profile visually useful and being kept active?

Each category has its own checks because I did not think one generic scoring rule would make sense across very different types of data.

The engine evaluates the available evidence, identifies gaps or opportunities and produces issues with severity, supporting metrics and recommendations. The overall score is useful for answering **“where should I look first?”**, while the recommendations answer **“what should I do when I get there?”**

For example, a missing field can be detected deterministically. If important profile content is missing, that check can fail and contribute to the score. If content exists but its quality needs judgment, an AI layer can help analyse or improve it rather than pretending that presence alone means quality.

The same principle applies to reputation. Code is better suited to questions such as how many reviews are unanswered, how many reviews meet a condition or whether sufficient evidence exists. AI is more useful for understanding review text, summarising themes or drafting a contextual response.

My principle was therefore:

**Use deterministic code where the answer can be measured reliably. Use AI where interpretation or generation genuinely adds value.**

I deliberately did not make the LLM responsible for the underlying score or basic factual calculations. The recommendations should remain traceable to the supplied data rather than depending on an opaque model decision.

**From audit to action**
------------------------

I wanted the output to go beyond saying that a location has a score of 60 or that a metric decreased.

A useful recommendation should answer:

**Why this location? → What is wrong? → What evidence supports it? → What should the operator do next?**

This is also why the prototype extends beyond a static audit.

I built a sample Google Business Profile management experience around the intelligence engine and a basic AI assistant with access to profile and audit capabilities. The intended real-world flow is:

**Connect Google account → Import locations → Gather profile and additional intelligence data → Audit each location → Prioritise issues → Recommend actions → Review or implement actions.**

The current project uses synthetic/sample data because I did not have approved access to the live Google Business Profile APIs. The Google connection and live write operations should therefore be treated as product direction, not as production-ready integration.

The AI assistant explores another part of that direction. Instead of requiring a small-business owner to understand every Google Business Profile optimisation concept or navigate every screen manually, the user could ask questions conversationally, understand why something matters and eventually ask the system to perform an approved action.

This became important to my product thinking because access to AI is reducing the knowledge gap between specialist marketers and ordinary business owners. I therefore see the long-term opportunity not simply as showing more analytics, but as turning specialist knowledge into guided and eventually semi-autonomous execution.

**What I deliberately did not build**
-------------------------------------

I deliberately kept parts of the system at prototype level because I was building it individually within a limited timeframe. My goal was to demonstrate the complete product direction while being clear about what is and is not production-ready.

I built the core audit/recommendation engine, a sample end-to-end profile-management experience and a basic AI agent with access to profile and audit capabilities.

I did not fully optimise every audit rule from a Google Business Profile subject-matter-expert perspective. There will be smaller signals, edge cases, category-specific differences and business-specific factors that need deeper research and real-world validation.

I also did not treat the AI agent as production-ready. Although the underlying agent and tools demonstrate the interaction model, it still needs extensive evaluation for hallucinations, ambiguous instructions, incorrect actions, permission boundaries and situations where human confirmation should be mandatory.

I also deliberately avoided claiming predicted uplift, guaranteed ranking improvement or revenue impact from recommendations when the supplied data cannot defensibly establish those outcomes.

**If I had another week**
-------------------------

My first priority would be **validation rather than feature count**.

I would review every audit rule, threshold, category weight and recommendation with deeper Google Business Profile domain expertise and test whether the engine is prioritising what actually matters to an operator. I would also investigate smaller signals and edge cases that the current rules may miss.

Second, I would make the AI assistant more specialised. Rather than one broad agent, I would explore stronger domain context and specialised capabilities around profile optimisation, reputation, local visibility, content and recommendations.

I would also improve longer-running agent workflows so the system can analyse a request, create a plan, use the appropriate tools, validate its results and continue through multiple steps rather than treating every interaction as an isolated prompt.

Before allowing autonomous writes to a live Google Business Profile, I would add stronger permission boundaries, confirmation for consequential changes, action logs and evaluation tests.

Finally, I would add real Google Business Profile integration, ingestion monitoring, incremental audit recomputation and operator feedback/outcome tracking. That feedback would allow the system to learn not only whether it found an issue, but whether its recommendation was actually useful.

The main lesson from this prototype was that I see this problem as roughly **70% domain understanding and decision design, and 30% software implementation**. Building a technically sophisticated system is not useful if it cannot explain the business problem it found or recommend a defensible next action. I therefore chose to start with the business problem and the data, and let the technology follow from those decisions.

Architecture and Local setup if you want to Test it 

I kept the intelligence engine separate from the AI layer so that the core audit remains deterministic, explainable and usable even when no LLM is configured.

The system has four main parts:

**Frontend — Next.js**The operator manages locations, reviews, posts, bookings and insights, runs audits, examines recommendations and interacts with the AI assistant.

**Backend — FastAPI + PostgreSQL**The backend owns authentication, location/profile data, audit results, recommendations and profile actions. PostgreSQL stores both the business data and the evidence behind each audit result.

**Audit engine — deterministic Python workers**An audit runs 67 checks across six independent categories: Profile, Reputation, Local Visibility, Operations, Performance and Content. Each worker evaluates its own data and returns findings and evidence. The results are then combined into the location health score and prioritised recommendations.

**AI layer — Gemini + LangGraph**AI is deliberately downstream of the deterministic engine. The audit decides **what is wrong**; AI helps with **what to write or how to act on it**. For example, code determines that a review is unanswered, while AI can draft an appropriate response. The conversational agent uses the application's existing functions as tools rather than maintaining a separate implementation of profile actions.

The main flow is:

Business / Profile Data

        ↓

PostgreSQL

        ↓

6 Audit Categories

        ↓

67 Deterministic Checks

        ↓

Findings + Evidence

        ↓

Weighted Health Score

        ↓

Prioritised Recommendations

        ↓

Optional AI Suggestions

        ↓

Operator Review / Action

Audits and agent turns run as background jobs using **Celery + Redis** because they can take longer than a normal HTTP request. Each job also owns a database record containing its status, progress and errors, so its state does not depend only on the Celery task.

The audit itself does not depend on AI. If the LLM is disabled or fails, deterministic checks, evidence, scoring and findings still work. Only AI-generated drafts are skipped.

For the prototype, Google Business Profile data is provided through a SampleGbpProvider backed by the assignment dataset. I attempted the live Google Business Profile API path, but the Cloud project did not have approved API quota. I therefore removed the non-working live implementation rather than presenting it as functional.

The provider abstraction keeps this boundary clean: once Google API access is available, the sample provider can be replaced without redesigning the audit, management or agent layers.

**Running locally**
-------------------

The prototype uses a **FastAPI backend, Next.js frontend, PostgreSQL database and Celery + Redis worker**.

### **Backend**

cd backend

cp .env.example .env

uv sync

uv run alembic upgrade head

uv run uvicorn app.main:app --reload

The backend automatically seeds the Brightpath Dental Group dataset on first boot.

Backend:

API      http://localhost:8000

Docs     http://localhost:8000/docs

Health   http://localhost:8000/api/v1/health

### **Celery worker**

Redis is required for the normal background-worker setup.

In a separate terminal:

cd backend

./start.sh                 # start worker in background

./start.sh --foreground    # alternatively run in current terminal

./stop.sh                  # stop worker

If Redis/Celery is not available, tasks can instead be executed inline:

cd backend

CELERY\_ALWAYS\_EAGER=true uv run uvicorn app.main:app --reload

In eager mode, a separate Celery worker is not required.

### **Frontend**

cd frontend

echo 'NEXT\_PUBLIC\_API\_URL=http://localhost:8000/api/v1' > .env.local

npm install

npm run dev

Then open:

http://localhost:3000

The seeded demo credentials are:

Email:    pawanpatrapp@gmail.com

Password: Pawan 2000

They are also prefilled on the sign-in screen.

### **AI setup**

I Used the google Vertex for Ai provider as i have credits on google accounts thats why.

Then configure:

LLM\_PROVIDER=vertex

VERTEX\_PROJECT=your-gcp-project

VERTEX\_LOCATION=global

VERTEX\_MODEL=gemini-3.1-flash-lite

SUGGESTIONS\_ENABLED=true

### **Verification (optional)**

cd backend && uv run pytest

cd backend && uv run ruff check .

cd frontend && npm run lint && npm run build

For detailed environment variables, AI configuration, troubleshooting and deployment instructions, see docs/tech/.
