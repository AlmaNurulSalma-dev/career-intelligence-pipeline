# Career Intelligence Pipeline - Architecture

## System Overview

End-to-end Azure data pipeline that ingests job listings from 3 sources (via 3 ingestion methods), transforms them using ADF and Synapse Spark, loads into Azure SQL, catalogs in Purview, and visualizes via Power BI.

## Data Flow Diagram
```
┌─────────────────────────────────────────┐
│         6 DATA SOURCES (3 types)        │
│  LinkedIn CSV | Config JSON | APIs      │
└────────────────────┬────────────────────┘
                     │
                     ▼
        ┌────────────────────────┐
        │   ADF Ingestion        │
        │  (Copy Activity)       │
        └────────┬───────────────┘
                 │
                 ▼
    ┌──────────────────────────────────┐
    │  ADLS Gen 2 - Raw Layer          │
    │  /raw/{source}/YYYY/MM/DD/       │
    └──────────────┬───────────────────┘
                   │
        ┌──────────┴──────────┐
        │                     │
        ▼                     ▼
   ┌─────────────┐    ┌──────────────────┐
   │ ADF Data    │    │ Synapse Spark    │
   │ Flow        │    │ (PySpark)        │
   │             │    │                  │
   │ - Flatten   │    │ - NLP extraction │
   │ - Dedup     │    │ - Skill scoring  │
   │ - Join      │    │ - Gap analysis   │
   │ - Normalize │    │ - Trends         │
   └─────────────┘    └──────────────────┘
        │                     │
        └──────────┬──────────┘
                   │
                   ▼
    ┌──────────────────────────────────┐
    │  ADLS Gen 2 - Transform Layer    │
    │  /transform/{category}/YYYY/MM/  │
    └──────────────┬───────────────────┘
                   │
                   ▼
         ┌─────────────────────┐
         │ Azure SQL Database  │
         │                     │
         │ - JobListings       │
         │ - SkillProfile      │
         │ - SkillGap          │
         │ - MarketTrends      │
         │ - SalaryBenchmarks  │
         │ - CompanyInsights   │
         └────────┬────────────┘
                  │
        ┌─────────┴──────────┐
        │                    │
        ▼                    ▼
   ┌─────────────┐    ┌──────────────────┐
   │  Purview    │    │  Power BI        │
   │  Catalog    │    │  Dashboard       │
   │             │    │                  │
   │ - Lineage   │    │ - Job Match      │
   │ - PII       │    │ - Skill Gap      │
   │ - Metadata  │    │ - Market Trends  │
   │             │    │ - Salary         │
   │             │    │ - App Timing     │
   │             │    │ - Company        │
   └─────────────┘    └──────────────────┘
        │                    │
        └─────────┬──────────┘
                  │
                  ▼
        ┌─────────────────────┐
        │  Logic Apps Email   │
        │  Weekly Digest      │
        └─────────────────────┘
```

## Components Breakdown

### 1. Data Ingestion Layer

**Sources:**
- LinkedIn Data Export (CSV) — Monthly skill profile refresh
- Config JSON (GitHub) — User preferences & custom skills
- Glints (Web Scraping) — Indonesia job listings
- JobStreet (Web Scraping) — Southeast Asia job listings
- Historical Data — Self-collected trends data (accumulated weekly)

**Ingestion Methods:**
- **Flat File CSV**: LinkedIn export (manual upload to ADLS)
- **Flat File JSON**: Config from GitHub (manual sync)
- **Web Scraping**: Glints & JobStreet (ADF + Python scripts, daily automated)

**Scraping Strategy (Robust):**
- Use Selenium for JavaScript rendering (both platforms use JS)
- Implement rotating proxies to avoid IP blocking
- Add random delays between requests (respect rate limits)
- Error handling & retry logic for resilience
- Monitoring: Track scraper health, detect failures
- Store raw HTML → parse into structured data
- Frequency: Daily run (02:00 UTC+7 Glints, 03:00 UTC+7 JobStreet)

**Historical Data Collection:**
- Week 1 baseline: Scrape Glints + JobStreet
- Week 2: Scrape again, compare skill frequencies
- Week 3: Scrape again, calculate trend growth rates
- Week 4+: Continue accumulating, trends become increasingly accurate
- Storage: ADLS `/raw/historical/` partition by week

### 2. Storage Layer

**Azure Data Lake Storage Gen 2 (ADLS Gen 2)**

*Raw Layer:*
```
/raw/
  ├── linkedin-csv/YYYY/MM/DD/
  ├── config-json/YYYY/MM/DD/
  ├── glints/YYYY/MM/DD/
  ├── jobstreet/YYYY/MM/DD/
  └── historical/YYYY/week-XX/
```

*Transform Layer:*
```
/transform/
  ├── normalized-jobs/YYYY/MM/DD/
  ├── skill-profiles/YYYY/MM/DD/
  ├── skill-gaps/YYYY/MM/DD/
  ├── market-trends/YYYY/MM/DD/
  └── salary-benchmarks/YYYY/MM/DD/
```

**Partitioning Strategy:**
- Date-based: `YYYY/MM/DD/` for daily partitioning
- Source-based: Separate folder per data source
- Reason: Enables incremental processing & cost optimization

### 3. Transformation Layer

**ADF Data Flow** (Structural Transformations):
- Parse & clean scraped HTML (convert to structured data)
- Flatten nested JSON (from Config JSON)
- Filter & remove nulls (drop invalid rows early)
- Remove unused columns (keep only relevant fields)
- Deduplication (remove duplicate job postings)
- Column normalization (standardize salary formats, dates, categories)
- Industry categorization (classify jobs by industry)
- Join datasets (enrich job listings with user profile)

**Azure Synapse Spark** (Complex Transformations):
- NLP Skill Extraction: Extract required skills from job descriptions using regex + NLP
- Match Score Calculation: Compare user skills vs. job requirements (0-100%)
- Skill Gap Analysis: Identify missing skills per job
- Market Trends: Aggregate trending skills week-over-week
- Salary Benchmarking: Compute salary ranges by role, industry, experience
- Application Timing: Detect hiring patterns (when roles are posted frequently)
- Interview Patterns: Common requirements per company

### 4. Loading Layer

**Azure SQL Database**

*6 Tables:*

**JobListings**
```sql
- job_id (PK)
- title, company, industry, location
- salary_min, salary_max, posted_date
- job_description, requirements
- source (glints, linkedin, kalibrr)
```

**SkillProfile**
```sql
- skill_id (PK)
- skill_name, proficiency (junior/mid/senior)
- years_of_experience
- is_willing_to_learn (bool)
```

**SkillGap**
```sql
- gap_id (PK)
- job_id (FK), skill_id (FK)
- is_required (bool)
- user_has (bool)
- proficiency_gap
```

**MarketTrends**
```sql
- trend_id (PK)
- skill_name
- frequency (count of postings)
- week_of_year
- growth_rate (%)
```

**SalaryBenchmarks**
```sql
- benchmark_id (PK)
- role_title, industry
- experience_level
- salary_p25, salary_p50, salary_p75
```

**CompanyInsights**
```sql
- company_id (PK)
- company_name
- avg_hiring_frequency
- common_required_skills
- avg_interview_round_count
```

### 5. Cataloging Layer

**Microsoft Purview**

- **Data Catalog**: Register ADLS, Azure SQL, ADF as sources
- **Lineage Tracking**: Track data flow from CSV → ADLS → Transform → SQL
- **PII Labeling**: Mark sensitive columns (salary, personal emails)
- **Glossary**: Define business terms (skill gap, market trend, match score)

### 6. Visualization Layer

**Power BI Dashboard** (6 Views)

1. **Job Match View**: Show matching jobs sorted by match %
2. **Skill Gap View**: Visualize missing skills per job
3. **Market Trends**: Trending skills over time (line chart)
4. **Salary Benchmarks**: Salary ranges by role & industry (box plot)
5. **Application Timing**: When to apply (hiring cycle patterns)
6. **Company Insights**: Common interview patterns & requirements

### 7. Notification Layer

**Logic Apps + Email**

### 7. Notification Layer

**Logic Apps + Email**

*Developer Alerts (On Failure):*
- Trigger: Pipeline failed OR data quality check failed OR cost exceeded threshold
- To: Developer email 
- Content: Error logs, failed step, recommended action
- Frequency: Immediate (urgent)
- Example: "Pipeline failed at Transform step — Synapse job timed out. Check Synapse logs."

*User Notifications (On Success):*
- Trigger: After successful pipeline run (weekly)
- To: End user email
- Frequency: Weekly digest
- Content: All 6 insights from Power BI dashboard:
  1. **Job Match**: Top 5 matching jobs + match percentages
  2. **Skill Gap**: Most frequently missing skills across job market
  3. **Market Trends**: Top 5 trending skills (week-over-week growth)
  4. **Salary Benchmarks**: Target salary range based on role + experience level
  5. **Application Timing**: Best time to apply (hiring cycle patterns per company)
  6. **Company Insights**: Interview patterns + common skill requirements per company

*Example Email Content:*
```
Subject: Your Weekly Career Intelligence Digest

Hi Alma,

Here's your weekly job market intelligence:

📌 TOP MATCHING JOBS
- Data Engineer at Company A (92% match)
- Analytics Engineer at Company B (88% match)
- (Top 5 total)

🎯 SKILL GAP
- Most missing: Apache Spark (45% of jobs require it)
- Second: Kubernetes (35% of jobs)

📈 TRENDING SKILLS THIS WEEK
- Apache Airflow: ↑ 15% (growing)
- Python: Stable (consistent high demand)

💰 SALARY BENCHMARKS
- Data Engineer (Mid-level, Jakarta): IDR 100-140M
- Your target: IDR 110-130M

⏰ APPLICATION TIMING
- Company A: Hiring surge — post every Monday
- Company B: Steady hiring — post weekly
- Best time to apply: This week

🏢 COMPANY INSIGHTS
- Company A: 3 interview rounds, focus on system design
- Company B: Values Apache Spark (60% of postings)

---
Ready to apply? Check your Power BI dashboard for detailed analysis.
```

**Flow:**
```
Pipeline runs
    ↓
Check if SUCCESS or FAILED
    ├→ If FAILED: Send developer alert immediately
    └→ If SUCCESS: Aggregate all 6 Power BI insights → Send user digest weekly
```

## Orchestration

**Azure Data Factory Pipelines**

- **Skill Profile Pipeline**: Daily trigger (if manual upload detected)
- **Job Listings Pipeline**: Daily trigger for all 3 APIs
- **Transform Pipeline**: After ingestion completes, trigger Synapse Spark
- **Load Pipeline**: After transform completes, load to Azure SQL

## Monitoring (6 Types)

1. **Pipeline Failure**: Did the job run? → Azure Monitor alerts
2. **Data Quality**: Null rates, schema drift → Custom checks in Synapse
3. **Performance**: Pipeline duration, slowdowns → Activity metrics
4. **Data Freshness**: Are sources updating? → Timestamp checks
5. **Cost**: Daily spend tracking → Azure Cost Management
6. **Business Metrics**: 0 new jobs = source failure → Custom metrics

## Technology Rationale

| Component | Why This Tool |
|---|---|
| ADLS Gen 2 | Hierarchical namespace, cost-effective, integrates with ADF/Synapse |
| ADF | Native Azure orchestration, UI-based pipeline design, Tumbling Window trigger support |
| ADF Data Flow | Low-code transformations, visual debugging, decent performance for structural changes |
| Synapse Spark | Heavy lifting (NLP, scoring), distributed compute, PySpark flexibility |
| Azure SQL | Structured output, Power BI native connector, cost-effective for analytics workload |
| Purview | Data governance, lineage tracking, PII detection (Azure ecosystem alignment) |
| Power BI | Easy dashboarding, shareable reports, integrates with Azure SQL natively |
| Logic Apps | Serverless notifications, email integration, no code/low code |

## Data Quality & Validation

- Schema validation: Check column names match expected schema
- Null rate monitoring: Flag if any column exceeds X% nulls
- Deduplication: Remove duplicate job postings (by job_id)
- Salary normalization: Handle different formats (hourly vs. monthly vs. yearly)
- API health checks: Verify API responses are returning data

## Cost Optimization

- **Incremental loads**: Only load new data (by date partition)
- **Pause Synapse**: Turn off when not processing
- **Delete old raw data**: Keep only last 90 days of raw layers
- **On-demand Spark**: Synapse on-demand pricing (cheaper than provisioned)

---

**Last Updated**: [March 30, 2026]