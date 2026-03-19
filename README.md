# AI Running Fitness Agent

A Python-based running analysis tool that ingests Garmin workout data, computes training metrics, applies deterministic injury-risk heuristics, generates an AI-assisted narrative summary, and exports the results to JSON, Markdown, and PDF.

## Current focus

This project is currently centered on four core areas:

- FIT parsing
- Weekly training metrics
- ACWR stability
- Injury-risk heuristics

The long-term goal is a maintainable AI running coach pipeline that can take raw activity data and turn it into structured, explainable training insights.

---

## What the project doe

Given a Garmin `.fit` file or supported `.csv` export, the app currently:

- parses run activity data into a consistent internal model
- computes recent workload and trend metrics
- evaluates deterministic risk flags
- generates a narrative interpretation using an OpenAI model
- saves outputs as:
  - JSON
  - Markdown
  - PDF

---

## Current architecture

The repo currently follows this flow:

```text
input file (.fit or .csv)
    ↓
parsing
    ↓
metric computation
    ↓
risk-flag evaluation
    ↓
LLM narrative generation
    ↓
markdown / PDF report output

---

## Module Responsibilities

app/io/fit_parser.py
Parses Garmin FIT files into internal Run objects.

app/io/csv_parser.py
Parses Garmin-style CSV exports into internal Run objects.

app/io/models.py
Defines the Run dataclass used throughout the app.

app/metrics/compute_metrics.py
Computes workload, weekly summaries, intensity split heuristics, rest/recovery spacing, monotony, strain, and related summary metrics.

app/flags/risk_flags.py
Applies deterministic, explainable injury-risk and training-balance heuristics.

app/llm/prompt.py
Builds the prompt used for narrative analysis.

app/llm/analyze.py
Calls the OpenAI API to generate interpretation, recommendations, and takeaways.

app/report/render_markdown.py
Renders a Markdown report from the structured payload.

app/report/render_pdf.py
Converts the Markdown report into a basic PDF.
