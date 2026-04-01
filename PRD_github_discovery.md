# PRD: Automated OSS Discovery & Queueing

**Status:** Draft
**Date:** 2026-03-31
**Working dir:** `/Users/chesterbeard/Desktop/opensourcescribes`

---

## Problem

The current repo queue (`github_urls.txt`) is populated manually, primarily by scanning TLDR newsletters and similar sources. This is labor-intensive, inconsistent, and does not scale. There is no deduplication beyond what the author remembers, meaning previously covered repos can resurface in the queue.

---

## Goal

Fully automate weekly discovery of 15 high-signal OSS repos — weighted toward AI tooling — ranked by a Mistral agent and written directly to `github_urls.txt` with no human review step required.

---

## Non-Goals

- Scraping email inboxes or newsletters (not practical)
- Covering non-GitHub-hosted projects (deferred)
- Topic-based strict filtering (star velocity + AI lean is sufficient signal)
- Manual approval workflow (fully automated)

---

## Success Criteria

- Each weekly run adds exactly 15 net-new repos to `github_urls.txt`
- No repo appears that has been covered before (deduplicated against permanent history)
- No archived or unmaintained repo (last commit > 30 days) appears in output
- Mistral provides a scored + annotated candidate list as a run artifact

---

## Functional Requirements

### 1. Discovery Layer (Source-Agnostic Architecture)

The discovery layer must be designed as a pluggable source registry. Each source is a class implementing a common interface (`DiscoverySource`) that returns a list of candidate repo URLs with raw metadata. This allows future sources (newsletters, aggregators, RSS feeds, social signals) to be added without modifying core logic.

**Sources in v1:**

| Source | Method | Timeframes |
|---|---|---|
| GitHub Trending | Scrape `github.com/trending` | Weekly, Monthly |
| GitHub Search API | Search by `stars`, `pushed`, `created` | Rolling 30-day window |

**GitHub Search API query strategy:**
- Sort by `stars` descending, filtered to repos pushed within last 30 days
- Separate queries targeting AI-adjacent topics: `topic:llm`, `topic:ai`, `topic:agents`, `topic:ml`, `topic:rag`, general top-starred recent repos as a catch-all
- This is not a hard topic filter — high-velocity non-AI repos can still pass through Mistral scoring

**Future source interface (design only, not built in v1):**
```python
class DiscoverySource:
    def fetch(self) -> list[RepoCandidate]:
        ...
```
Planned future sources: curated newsletter RSS feeds, GitHub Explore, Hacker News "Ask HN: What are you building" threads.

---

### 2. Data Fetching

For every candidate URL surfaced by discovery, fetch the following via GitHub REST API:

- `owner`, `repo`, `full_name`
- `stargazers_count`, `forks_count`
- `language`
- `description`
- `topics[]`
- `pushed_at` (last commit date)
- `archived` (boolean)
- `created_at`
- `homepage`
- README content (via `/repos/{owner}/{repo}/readme`, base64-decoded)
- **Star velocity** — computed as `(current_stars - cached_stars) / days_since_cache` using `github_stats_cache.json` as the historical baseline. The cache stores star counts with timestamps; velocity is the delta divided by elapsed days. Repos not yet in the cache have no velocity score and are ranked lower by Mistral.

---

### 3. Filtering (Pre-Mistral)

Hard filters applied before sending candidates to Mistral — these are non-negotiable disqualifiers:

| Filter | Rule |
|---|---|
| Archived | Exclude if `archived == true` |
| Unmaintained | Exclude if `pushed_at` older than 30 days |
| Already covered | Exclude if URL present in `repo_history.json` |
| Already queued | Exclude if URL present in current `github_urls.txt` |
| No description | Exclude if `description` is null or empty |
| Fork | Exclude if `fork == true` |

No minimum star count filter. Star velocity is the primary ranking signal, handled by Mistral.

---

### 4. Mistral Scoring Agent

After hard filtering, remaining candidates are passed to a Mistral agent for scoring and selection.

**Model:** `mistral-small` (cost-efficient for batch scoring; upgrade to `mistral-large` if reasoning quality is insufficient)

**Input per candidate:**
```
Repo: {full_name}
Description: {description}
Language: {language}
Topics: {topics}
Stars: {stargazers_count}
Star velocity (30d): {velocity} stars/day
Last commit: {pushed_at}
README (truncated to 2000 chars): {readme_excerpt}
```

**Scoring prompt:**
The agent is instructed to score each repo 1–10 on:
- **Momentum** (star velocity, recency of activity)
- **Content potential** (is this interesting to explain to a developer/tech audience?)
- **AI/tooling relevance** (soft preference, not a hard gate)

The agent returns for each candidate:
```json
{
  "repo": "owner/name",
  "score": 8.2,
  "reason": "One-sentence reason why this is worth covering"
}
```

Top 15 by score are selected. The full scored list is saved as a run artifact (see Output).

**Implementation:** Use `mistralai` Python SDK with function calling or structured output mode to enforce JSON response schema.

---

### 5. Deduplication & History

**New file: `repo_history.json`**

A permanent append-only log of every repo that has ever been added to the queue. Structure:

```json
{
  "owner/repo": {
    "url": "https://github.com/owner/repo",
    "added_at": "2026-03-31T00:00:00Z",
    "run_id": "2026-03-31"
  }
}
```

**Rules:**
- Before writing to `github_urls.txt`, check both `repo_history.json` AND current `github_urls.txt`
- After writing, append all 15 selected repos to `repo_history.json`
- `repo_history.json` is never truncated — it grows indefinitely as the permanent dedup source of truth
- `github_urls.txt` remains the active processing queue and can be cleared between runs as repos are consumed

---

### 6. Output

**Per run, the tool produces:**

1. **`github_urls.txt`** — 15 new URLs appended (or written, depending on queue state)
2. **`repo_history.json`** — updated with 15 new entries
3. **`discovery_runs/YYYY-MM-DD.json`** — run artifact containing:
   - All candidates surfaced (pre-filter count)
   - Post-filter candidate list
   - Full Mistral-scored list with scores and reasons
   - Final 15 selected

The run artifact is for auditability — so you can review why Mistral picked or skipped a repo after the fact.

---

### 7. Scheduling

Run manually on demand — no cron or Prefect scheduling required. The user manually clears consumed repos from `github_urls.txt` before each run, then triggers the discovery script directly. The script always appends 15 new URLs regardless of current queue state.

---

## Architecture

```
┌─────────────────────────────────────┐
│         Discovery Layer             │
│  ┌──────────────┐ ┌───────────────┐ │
│  │ GitHub       │ │ GitHub Search │ │
│  │ Trending     │ │ API           │ │
│  │ (wk + mo)    │ │ (30d window)  │ │
│  └──────┬───────┘ └───────┬───────┘ │
│         └────────┬─────────┘        │
└──────────────────┼──────────────────┘
                   │ raw candidate URLs
                   ▼
        ┌──────────────────────┐
        │  GitHub REST API     │
        │  Data Fetcher        │
        │  (stats + README)    │
        └──────────┬───────────┘
                   │ enriched candidates
                   ▼
        ┌──────────────────────┐
        │  Hard Filter         │
        │  (archived, stale,   │
        │   dedup, no desc)    │
        └──────────┬───────────┘
                   │ filtered candidates
                   ▼
        ┌──────────────────────┐
        │  Mistral Agent       │
        │  Score + Rank + Reason│
        └──────────┬───────────┘
                   │ top 15
                   ▼
        ┌──────────────────────┐
        │  Output Writer       │
        │  github_urls.txt     │
        │  repo_history.json   │
        │  discovery_runs/     │
        └──────────────────────┘
```

---

## Files Introduced

| File | Purpose |
|---|---|
| `github_discovery.py` | Main discovery script (new) |
| `repo_history.json` | Permanent dedup history (new) |
| `discovery_runs/` | Per-run audit artifacts directory (new) |
| `github_urls.txt` | Existing — appended to by discovery script |
| `github_stats_cache.json` | Existing — used for star velocity baseline |

---

## Open Questions / Future

- **Newsletter sources:** TLDR and similar newsletters publish RSS or structured data in some cases — worth a future spike to find parseable sources that don't require email access. Email scraping is out of scope.
- **Mistral model tier:** Start with `mistral-small`; if scoring feels shallow on README analysis, bump to `mistral-large` for that step only.

## Resolved Decisions

| Question | Decision |
|---|---|
| Queue cap behavior | User manually clears `github_urls.txt` before each run; script always appends 15 |
| Star velocity source | Use `github_stats_cache.json` as historical baseline; no Stargazers API pagination |
| Scheduling | Manual on-demand execution, no cron |
