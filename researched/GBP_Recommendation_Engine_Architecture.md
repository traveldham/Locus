# Google Business Profile Recommendation Engine — Technical Architecture Plan

## 1. Goal

Build a reusable intelligence platform for Google Business Profile (GBP) locations that can:

- ingest profile, performance, review, ranking, competitor, media, post, attribute, hours, search-term, and booking data;
- understand the current condition of each business location;
- identify weaknesses, anomalies, missed opportunities, and declining trends;
- generate specific, evidence-backed recommendations;
- prioritize recommendations by likely business impact;
- learn from recommendation outcomes over time;
- work across different business categories, not only dental clinics.

The core idea is:

```text
Google Business Profile + Business Data
                ↓
        Data Ingestion Layer
                ↓
      Normalized Data Platform
                ↓
          Feature Engine
                ↓
 ┌───────────────────────────────────┐
 │ Recommendation Intelligence      │
 │                                   │
 │ Rules + Statistics + ML + NLP    │
 │ + Causal/Uplift Learning          │
 └───────────────────────────────────┘
                ↓
       Recommendation Ranker
                ↓
 Recommendation + Evidence + Priority
                ↓
          Human Approval
                ↓
        Action / Execution
                ↓
          Measure Outcome
                ↓
              Learn
```

---

## 2. Data Model

The current dataset is location-centric.

```text
LOCATION
   |
   ├── Profile information
   ├── Hours
   ├── Attributes
   ├── Media
   ├── Daily performance
   ├── Search terms
   ├── Reviews
   ├── Review replies
   ├── Posts
   ├── Tracked keywords
   ├── Keyword rankings
   ├── Competitors
   └── Bookings
```

The common location identifier should remain the main join key.

### Main source tables

- `locations`
- `location_hours`
- `location_daily_kpis`
- `location_search_terms_monthly`
- `attribute_catalog`
- `location_attributes`
- `location_media_summary`
- `reviews`
- `review_replies`
- `posts`
- `booking_requests`
- `tracked_keywords`
- `keyword_rank_weekly`
- `competitor_ranks_weekly`

These tables operate at different time grains.

```text
Profile             → snapshot
Hours               → configuration
Media               → snapshot

KPIs                → daily
Keyword rankings    → weekly
Competitors         → weekly
Search terms        → monthly

Reviews             → event
Replies             → event
Posts               → event
Bookings            → event
```

Do not directly flatten every source into one giant table.

Instead create consistent feature snapshots such as:

```text
Location × Day
Location × Week
Location × Month
```

---

## 3. Production Ingestion Architecture

For a real product, data should come through APIs/connectors instead of manually uploaded CSVs.

```text
             External Sources

GBP Business Information
GBP Performance
GBP Reviews
GBP Posts
GBP Media
GBP Notifications
Rank Tracking Provider
CRM / Booking Platform
Website Analytics
Call Tracking
        │
        ▼
   Connector Layer
        │
        ▼
     Raw Staging
        │
        ▼
 Data Validation Layer
        │
        ▼
 Normalized Data Store
```

Use both:

- **event-based ingestion** for reviews, changes, alerts;
- **scheduled batch ingestion** for performance, rankings, competitors, search terms.

Example:

```text
New review
   ↓
Event
   ↓
Review ingestion
   ↓
NLP analysis
   ↓
Potential recommendation
```

And:

```text
Nightly job
   ↓
Performance refresh
   ↓
Feature refresh
   ↓
Recommendation refresh
```

---

## 4. Data Quality Layer

Before any ML model sees the data:

```text
Incoming Data
     ↓
Schema Validation
     ↓
Date Validation
     ↓
Duplicate Detection
     ↓
Referential Integrity
     ↓
Coverage Checks
     ↓
Outlier / Impossible-Value Checks
     ↓
Quarantine Invalid Records
     ↓
Feature Pipeline
```

Important checks:

- missing `location_id`;
- duplicate primary keys;
- future-dated events;
- unknown locations;
- inconsistent time windows;
- missing required fields;
- metric values below zero where impossible;
- incomplete time series;
- unexpected schema changes.

---

## 5. Recommended Database Structure

```text
organizations
accounts
locations
location_snapshots
location_hours
location_attributes
location_media

performance_daily
search_terms_monthly

reviews
review_replies
review_analysis

posts
bookings

tracked_keywords
keyword_rank_history
competitor_snapshots

feature_snapshots

recommendations
recommendation_evidence
recommendation_actions
recommendation_outcomes

model_predictions
model_registry
```

### Critical learning tables

#### recommendations

```text
recommendation_id
location_id
generated_at
recommendation_type
priority
confidence
expected_impact
model_version
status
```

#### recommendation_actions

```text
recommendation_id
shown_at
accepted
rejected
executed
executed_at
execution_type
```

#### recommendation_outcomes

```text
recommendation_id
metric
baseline_value
after_value
measurement_window
uplift
```

These tables become the future training dataset.

---

## 6. Feature Engine

ML should work on meaningful business features rather than raw CSV rows.

### Review Features

```text
average_rating_30d
average_rating_90d
review_volume_30d
review_velocity
reply_rate_30d
average_reply_delay
negative_review_rate
one_star_rate
rating_trend
review_topic_distribution
review_sentiment_distribution
```

### Visibility Features

```text
maps_impressions_7d
maps_impressions_30d
search_impressions_30d
impression_growth_30d
mobile_share
desktop_share
```

### Engagement / Intent Features

```text
website_click_rate
call_rate
direction_rate
conversation_rate
booking_rate
```

### Ranking Features

```text
average_rank
median_rank
top_3_rate
top_10_rate
not_found_rate
rank_change_4w
rank_volatility
local_pack_rate
```

### Competitor Features

```text
review_gap
rating_gap
photo_gap
competitor_rank_gap
competitor_review_growth
competitor_photo_growth
```

### Profile Features

```text
description_present
description_length
website_present
phone_present
hours_complete
attribute_completeness
photo_count
photo_recency
video_count
profile_photo_present
cover_photo_present
post_frequency
```

### Booking Features

```text
booking_request_volume
booking_confirmation_rate
booking_completion_rate
cancellation_rate
no_show_rate
source_mix
lead_to_booking_rate
```

---

## 7. Cross-Industry Normalization

Absolute values should not be compared blindly across industries.

Instead of only:

```text
review_count = 500
```

calculate:

```text
review_percentile_in_category
review_percentile_in_city
review_percentile_in_market
review_count_vs_peer_median
review_velocity_percentile
```

Build peer cohorts using:

```text
business category
country
region
city / metro
location maturity
brand type
business size
urban / suburban / rural
```

Example:

```text
Dentist
Austin
Mature location
Multi-location brand
Urban
```

This gives much fairer comparisons.

---

## 8. Recommendation Intelligence Architecture

Use a hybrid system.

```text
                 FEATURE STORE
                      │
      ┌───────────────┼────────────────┐
      │               │                │
      ▼               ▼                ▼
 Deterministic    Statistical        ML Models
    Rules          Detection
      │               │                │
      └───────────────┼────────────────┘
                      ▼
              Candidate Actions
                      │
                      ▼
             Recommendation Ranker
                      │
                      ▼
               Top Recommendations
```

---

## 9. Layer A — Deterministic Rules

Use rules when the answer is objectively known.

Examples:

```text
website missing
profile not verified
missing business hours
missing description
missing cover photo
missing profile photo
critical attribute unset
no posts for long period
```

Example rule:

```python
if not location.website_url:
    create_recommendation(
        type="profile_completion",
        action="Add website URL",
        priority="high"
    )
```

Rules are appropriate when ML adds no value.

---

## 10. Layer B — Statistical / Anomaly Detection

Use anomaly detection for unexpected behavior.

Example:

```text
Weekly calls:

145
151
148
153
149
147
72
```

Possible techniques:

- Robust Z-score
- Median Absolute Deviation
- Isolation Forest
- Local Outlier Factor
- Seasonal anomaly detection

Output:

```text
Unusual drop in calls

Observed: 72
Expected range: 137–162
Severity: High
Confidence: 96%
```

---

## 11. Layer C — Trend Detection

Detect meaningful direction over time.

Examples:

- rankings declining;
- calls declining;
- bookings improving;
- review velocity falling;
- search impressions increasing;
- local-pack presence dropping.

Possible approaches:

- rolling averages;
- exponentially weighted averages;
- slope / regression;
- change-point detection;
- seasonal baseline models.

---

## 12. Layer D — Forecasting

Forecast key business metrics.

Possible targets:

```text
bookings_next_30d
calls_next_30d
website_clicks_next_30d
directions_next_30d
visibility_next_30d
average_rank_next_4w
```

Recommended first models:

- LightGBM
- CatBoost
- XGBoost
- classical time-series baselines

Start with gradient-boosted tree models because GBP data is mainly structured/tabular.

Do not start with large neural networks unless data volume later justifies them.

---

## 13. Layer E — Review Intelligence

Reviews are unstructured text and should have their own NLP pipeline.

```text
Review Text
    ↓
Language Detection
    ↓
Sentiment
    ↓
Embeddings
    ↓
Topic Clustering / Classification
    ↓
Urgency / Complaint Detection
    ↓
Trend Aggregation
```

Example output:

```text
Positive topics
---------------
Staff friendliness       34%
Cleanliness              21%
Service quality          19%

Negative topics
---------------
Waiting time             31%
Billing                  23%
Parking                  17%
Appointment handling     15%
```

Then identify change:

```text
Waiting-time complaints

Previous 90 days: 9%
Last 30 days: 27%
```

Recommendation:

```text
Investigate appointment delays.
Waiting-time complaints have increased materially.
```

LLMs can summarize the evidence, but should not invent the evidence.

---

## 14. Candidate Recommendation Generation

Do not ask one model to invent arbitrary recommendations.

Create a controlled action catalog.

Example actions:

```text
improve_review_response
resolve_negative_review_pattern
add_recent_photos
add_video
update_description
complete_attributes
fix_business_hours
improve_keyword_visibility
recover_local_pack_loss
publish_post
improve_booking_conversion
investigate_call_drop
improve_search_term_coverage
```

Each detector/model generates candidate actions.

---

## 15. Recommendation Ranking

Before supervised training data exists, use a transparent priority score.

```text
Recommendation Score =

Severity
× Confidence
× Potential Impact
× Actionability
× Business Relevance
```

Example:

```text
Review response problem

Severity            0.87
Confidence          0.98
Potential impact    0.72
Actionability       0.95
Business relevance  0.90
```

Use this only as a relative priority score.

Do not falsely present it as a probability of revenue gain.

---

## 16. Business Goal Configuration

Different categories care about different outcomes.

### Dentist

```text
Primary:
bookings

Secondary:
calls
website clicks
```

### Restaurant

```text
Primary:
directions
reservations
orders
```

### Hotel

```text
Primary:
bookings
website clicks
calls
```

### Plumber

```text
Primary:
calls
conversations
```

### Retail

```text
Primary:
directions
website visits
```

Store business goals separately.

```json
{
  "category": "dentist",
  "primary_goal": "bookings",
  "secondary_goals": [
    "calls",
    "website_clicks"
  ]
}
```

Recommendation ranking should depend on these goals.

---

## 17. ML Model Strategy

### Early Stage

Use:

```text
Rules
+
Statistical detection
+
Unsupervised ML
+
NLP
+
Transparent scoring
```

Recommended algorithms:

| Problem | Approach |
|---|---|
| missing profile information | deterministic rules |
| profile completeness | rules |
| unusual performance | anomaly detection |
| trends | statistical models |
| forecasting | CatBoost / LightGBM |
| review sentiment | classifier |
| review topics | embeddings + clustering |
| opportunity ranking | heuristic score initially |
| explanation | evidence + LLM |

---

## 18. Why Not Train a Universal ML Model Immediately?

The current sample is not sufficient for a production universal model because:

- only one organization is represented;
- only one business category is represented;
- only 12 locations exist;
- there are no recommendation labels;
- there are no historical action-outcome labels.

Unsupervised models can identify unusual patterns.

They cannot reliably answer:

```text
Which action will produce the largest business improvement?
```

To answer that, the system needs historical action-outcome data.

---

## 19. Recommendation Learning Loop

From day one, collect:

```text
Location
+
Context
+
Recommendation
+
Accepted / Rejected
+
Executed / Not Executed
+
Outcome
```

Example:

```text
Recommendation:
Add 20 recent photos

Shown:
Jan 2

Accepted:
Jan 3

Executed:
Jan 5

Before:
Maps views = 4,200
Calls = 112

After:
Maps views = 4,730
Calls = 126
```

Now a real training example exists.

---

## 20. Training Row for Recommendation Learning

Build rows like:

```text
Context Features
---------------
category
market
location age
baseline visibility
baseline ranking
rating
review count
photo count
competitor gap
search demand
seasonality

Treatment
---------
add_photos

Outcome
-------
change_in_bookings_30d
change_in_calls_30d
change_in_visibility_30d
```

This allows the system to learn action effectiveness.

---

## 21. Causal / Uplift ML

Eventually the important question becomes:

```text
Which action is most likely to CAUSE improvement
for this specific business?
```

Possible models:

- Causal Forest
- T-Learner
- X-Learner
- DR-Learner
- Uplift Trees

Example:

```text
Expected bookings without action:
100

Expected bookings after adding photos:
104

Estimated uplift:
+4


Expected bookings after improving reviews:
117

Estimated uplift:
+17
```

Then rank:

```text
1. Improve review strategy
2. Add media
```

This is much stronger than simple anomaly detection.

---

## 22. Contextual Bandit — Mature Product

For a mature system:

```text
Context
   ↓
Choose Recommendation
   ↓
Observe Reward
   ↓
Update Policy
```

Where:

```text
Context =
business state + category + market + history

Action =
candidate recommendation

Reward =
business improvement
```

Example:

```text
Dentist A
→ Review recommendation
→ +12 booking uplift

Restaurant B
→ Photo recommendation
→ +8% direction requests

Plumber C
→ Hours recommendation
→ +15% calls
```

Over time the system learns the next best action.

---

## 23. Global + Category-Specific Models

A universal product should not immediately create one model per category.

Start with:

```text
Global Model
+
Peer Normalization
+
Category Features
```

Later, when enough data exists:

```text
                       Global Model
                            │
                  Category Representation
                            │
         ┌──────────────────┼──────────────────┐
         ▼                  ▼                  ▼
    Healthcare          Restaurants         Services
      Expert              Expert             Expert
         │                  │                  │
         └──────────────────┼──────────────────┘
                            ▼
                     Recommendation
```

This supports cold-start categories while allowing specialization later.

---

## 24. Structured Recommendation Output

Never return only free-form text.

Example:

```json
{
  "location_id": "LOC-006",
  "recommendation_type": "review_response",
  "title": "Increase review response coverage",
  "priority": "HIGH",
  "confidence": 0.91,
  "reason": "Review response coverage is below comparable locations.",
  "evidence": [
    {
      "metric": "reply_rate",
      "location_value": 33.7,
      "peer_median": 61.4
    }
  ],
  "suggested_action": {
    "type": "reply_to_reviews",
    "target": "recent_unanswered_reviews"
  },
  "model_version": "recommendation-v1"
}
```

Everything should remain traceable.

---

## 25. Evidence Layer

Keep evidence generation separate from language generation.

```text
Model / Rule Output
       ↓
Evidence Builder
       ↓
Structured Facts
       ↓
LLM Explanation
       ↓
Human-Friendly Recommendation
```

Avoid:

```text
All raw business data
       ↓
LLM
       ↓
"Tell me what to recommend"
```

The LLM should explain grounded evidence, not become the core decision engine.

---

## 26. Backend Architecture

Recommended production stack:

```text
                     FRONTEND
                      Next.js
                         │
                         ▼
                    API Gateway
                         │
                         ▼
                     FastAPI
       ┌─────────────────┼─────────────────┐
       │                 │                 │
       ▼                 ▼                 ▼
 Location API     Recommendation API    Action API
       │                 │                 │
       └─────────────────┼─────────────────┘
                         ▼
                     PostgreSQL
                         │
                    Analytics Store
                         │
                      BigQuery
                         │
                   Feature Pipeline
                         │
             ┌───────────┼───────────┐
             ▼           ▼           ▼
           Rules       ML Models      NLP
             │           │           │
             └───────────┼───────────┘
                         ▼
              Recommendation Service
```

Suggested stack:

| Layer | Technology |
|---|---|
| Backend | FastAPI / Python |
| Operational DB | PostgreSQL |
| Analytics | BigQuery |
| Raw storage | Cloud Storage |
| Events | Pub/Sub |
| Cache | Redis |
| Transformations | dbt |
| ML | Python |
| Tabular models | CatBoost / LightGBM |
| General ML | scikit-learn |
| NLP | embeddings + classifiers |
| Experiments | MLflow |
| Explainability | SHAP |
| Frontend | Next.js |
| Infrastructure | GCP |

---

## 27. Recommendation vs Execution

Keep these separate.

```text
Recommendation Generated
          ↓
User Reviews Evidence
          ↓
Approve / Reject
          ↓
Action Service
          ↓
External API / Manual Task
          ↓
Record Execution
          ↓
Measure Outcome
          ↓
Learn
```

This prevents automatic unsafe or unwanted changes.

---

## 28. Competitor Intelligence

Competitor rankings may come from a separate ranking provider.

```text
GBP Data
                     → Location Intelligence Store
       /
Rank Tracking Provider
               Competitor Data
```

Join competitor observations using:

```text
location
keyword
geo area
device
date
```

Useful competitor features:

```text
our_rank_vs_competitor
review_gap
rating_gap
photo_gap
competitor_growth
local_pack_gap
```

---

## 29. Training Pipeline

```text
Raw Data
    ↓
Validation
    ↓
Normalized Events
    ↓
Feature Snapshots
    ↓
Training Dataset Builder
    ↓
Time-Based Train / Validation / Test Split
    ↓
Model Training
    ↓
Offline Evaluation
    ↓
Model Registry
    ↓
Shadow Deployment
    ↓
A/B Test
    ↓
Production
```

For time series, avoid random train/test splits.

Example:

```text
Train: Jan–Jun
Validation: Jul
Test: Aug
```

---

## 30. Evaluation Metrics

Do not judge the product only by model accuracy.

Track:

```text
prediction quality
recommendation acceptance rate
recommendation completion rate
business uplift
false recommendation rate
recommendation coverage
evidence correctness
user trust
```

Ultimate metrics may be:

```text
incremental bookings per recommendation
incremental calls per recommendation
incremental direction requests
incremental revenue
```

---

## 31. Recommended Implementation Phases

### Phase 1 — Assignment / Prototype

Build:

```text
Data loader
↓
Validation
↓
Feature engineering
↓
Rules
↓
Statistical detection
↓
Unsupervised anomaly detection
↓
Review NLP
↓
Priority scoring
↓
Evidence-backed recommendation JSON
↓
Simple UI
```

Suggested weighting:

```text
70% deterministic + statistical intelligence
20% unsupervised ML / NLP
10% LLM explanation
```

---

### Phase 2 — Real SaaS MVP

Add:

```text
GBP connectors
multi-tenant backend
scheduled ingestion
event ingestion
feature store
category peer benchmarking
recommendation tracking
execution tracking
outcome tracking
```

---

### Phase 3 — Learning Recommendation Engine

Add:

```text
supervised opportunity ranking
forecasting
learning-to-rank
action effectiveness models
A/B testing
```

---

### Phase 4 — Next-Best-Action Platform

Add:

```text
causal inference
uplift modeling
contextual bandits
category experts
adaptive recommendation policy
```

---

## 32. Final Architecture Decision

The correct architecture is NOT:

```text
ML instead of backend
```

and NOT:

```text
CRUD instead of ML
```

It is:

```text
CRUD / Data Platform
        +
Rules
        +
Feature Store
        +
Statistics
        +
ML
        +
NLP
        +
Causal Learning
        +
Recommendation Ranker
        +
LLM Explanation
        +
Human Approval
        +
Outcome Learning
```

### Role of each layer

```text
CRUD / Backend
→ stores and serves data

Rules
→ catches deterministic issues

ML
→ detects patterns, anomalies and predicts outcomes

NLP
→ understands reviews and unstructured text

Causal / Uplift Models
→ estimate which action is likely to create improvement

Recommendation Ranker
→ selects what matters most

LLM
→ explains findings clearly

Outcome Tracking
→ creates future training data
```

The long-term goal is to move from:

```text
"What looks wrong?"
```

to:

```text
"What action should this business take next?"
```

and finally:

```text
"Which action is most likely to create measurable improvement
for this specific business right now?"
```

That is the target architecture for a scalable Google Business Profile recommendation intelligence platform.
