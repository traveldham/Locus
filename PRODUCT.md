# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Stack

- Frontend: the existing `frontend/` Next.js 16, React 19, TypeScript, Tailwind CSS 4, and Tailgrids admin template.
- Backend: FastAPI with SQLAlchemy 2 and Alembic.
- Database: the local PostgreSQL database named `locus`.

## Users

The primary users are operators and managers responsible for performance across many physical business locations. They need one secure workspace that will eventually show which locations need attention and why.

## Product Purpose

Locus Intelligence is a multi-location decision-support application. The current milestone establishes the reliable product foundation: authenticated users, organizations, a protected application shell, and a typed frontend-to-backend connection. Domain intelligence comes later.

## Positioning

The eventual product will turn fragmented location signals into prioritized, evidence-backed actions rather than stopping at metric reporting. This milestone must preserve that direction without inventing unfinished intelligence features.

## Operating Context

Users sign in to an organization workspace and operate from a responsive web dashboard. The initial application is evaluated locally and should be easy for another engineer or agent to extend.

## Capabilities and Constraints

- Current scope: FastAPI foundation, PostgreSQL persistence, migrations, authentication, organizations, protected frontend routes, account context, and a clean branded application shell.
- Out of scope for this milestone: CSV ingestion, recommendation scoring, analytics, competitor intelligence, LLM features, and final assignment output.
- Adapt the existing NextAdmin template instead of rebuilding its component system.
- Remove mock data, demo navigation, and visible NextAdmin branding from the product experience.
- Keep secrets out of source control and provide safe environment examples.

## Brand Commitments

- Product name: Locus Intelligence.
- Public reference: `https://locus-intelligence.com/`.
- Reuse public first-party logo/favicon assets and the recognizable brand palette where technically appropriate.
- The application should feel focused, operational, and enterprise-ready rather than like a generic template.

## Evidence on Hand

- Assignment brief: `locus-intelligence-assignment/README.md`.
- Dataset dictionary: `locus-intelligence-assignment/DATA.md`.
- Synthetic data: `locus-intelligence-assignment/data/`.
- Existing application scaffold: `frontend/`.
- Public brand source: `https://locus-intelligence.com/`.
- No customer testimonials, production analytics, or validated product outcomes may be fabricated.

## Product Principles

- Establish trustworthy foundations before domain intelligence.
- Keep every future insight traceable to evidence.
- Favor clear operational actions over decorative dashboards.
- Preserve explicit boundaries between deterministic logic and generated language.
- Keep the system easy to inspect, run, and extend.

## Accessibility & Inclusion

Maintain keyboard access, visible focus states, semantic form labels and errors, responsive layouts, and WCAG AA text contrast across light and dark themes.
