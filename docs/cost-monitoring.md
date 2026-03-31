# Azure Cost Monitoring & Optimization Guide

## Overview

This project uses a **pay-as-you-go Azure subscription**. Costs can accumulate quickly if resources are left running. This guide helps you monitor spending and optimize costs throughout the project.

## Cost Baseline (Monthly Estimates)

| Resource | Tier | Est. Monthly Cost | Notes |
|---|---|---|---|
| ADLS Gen 2 (Storage) | Standard | $5-10 | Depends on data volume stored |
| Azure SQL Database | Standard (S1) | $15-20 | Can pause compute to reduce cost |
| Synapse Analytics | On-demand Spark | $5-15 | Only charged during job execution |
| Azure Data Factory | Pay-per-run | $1-5 | Minimal for learning phase |
| Azure Key Vault | Standard | $0.60 | Fixed monthly cost |
| Microsoft Purview | Basic | $5-10 | Fixed monthly cost |
| **TOTAL (Optimized)** | — | **$30-60** | With pausing & cleanup |

## How to Monitor Costs in Azure Portal

### Step 1: Access Cost Management
1. Go to **Azure Portal** (portal.azure.com)
2. Search for **"Cost Management + Billing"**
3. Select your subscription
4. Click **"Cost Analysis"** in left menu

### Step 2: View Spending
- **By time period**: Select date range (today, last 7 days, last 30 days, custom)
- **By resource**: See which resources cost the most
- **By service**: Group by service type (Compute, Storage, etc.)
- **Daily breakdown**: Identify which day had highest spending

### Step 3: Set Budget Alerts
1. Go to **Cost Management** → **Budgets**
2. Click **"+ Add"** to create new budget
3. Set monthly budget: **$100** (recommended for learning)
4. Set alert threshold: **80%** (alert when spend reaches $80)
5. Add email: `blablabla@gmail.com`
6. Enable notifications

## Cost Optimization Strategies

### Strategy 1: Pause Synapse Workspace (When Not Using)

Synapse charges per second when running. When idle, pause to save cost.

**How to pause:**
1. Go to Azure Portal → **Synapse Analytics**
2. Select your workspace (`synapse-career-intel`)
3. Click **"Pause"** button
4. Takes ~2 minutes to pause

**Cost saving:** ~$5-15/month if paused 50% of the time

**When to stop running Synapse jobs:**
- After completing transformation jobs
- Don't let jobs run idle in background
- Cancel any test jobs that finished executing

**Cost implication:** On-demand Spark only charges during execution, so as long as no jobs running = no cost

**When to resume:**
- Before running pipeline
- Resume → takes ~2 minutes to start

---

### Strategy 2: Delete Old Raw Data (Archive Historical Layers)

ADLS storage charges per GB stored. Old raw data can be deleted after transformation.

**How to delete:**
1. Go to Azure Portal → **Storage Accounts** → `sa-career-intelligence`
2. Go to **Containers** → **raw** folder
3. Delete old date partitions (keep only last 30 days)
```
   /raw/glints/2026/01/  ← DELETE (old)
   /raw/glints/2026/03/  ← KEEP (recent)
```

**Cost saving:** ~$2-5/month if deleting monthly old data

---

### Strategy 3: Right-Size Azure SQL Database

SQL Database has fixed compute cost based on tier. For learning, use minimal tier.

**Current recommendation:**
- Tier: **Standard (S1)** — ~$15-20/month
- Alternative: **Basic** — ~$5-10/month (slower, but cheaper for learning)

**How to downsize:**
1. Go to Azure Portal → **Azure SQL Databases** → `career-intelligence-db`
2. Click **"Pricing tier"**
3. Select **"Basic"** (cheaper) or keep **"Standard"**
4. Apply changes

**Cost saving:** ~$5-10/month by downgrading to Basic

---

### Strategy 4: Delete Test/Temporary Data

Every test run creates data in ADLS & SQL. Clean up after testing.

**How to clean:**
1. ADLS: Delete test folders in `/transform/` and `/raw/`
2. SQL: Delete test tables with `DROP TABLE test_*`
3. Power BI: Delete test dashboards

**Cost saving:** ~$1-3/month from reduced storage

---

### Strategy 5: Use ADF Triggers Wisely

ADF charges per trigger run. Avoid excessive test runs.

**How to optimize:**
- Disable triggers during development (run manually only)
- Enable triggers only when pipeline is stable & ready for production
- Schedule infrequent triggers (e.g., daily vs. every hour)

**Cost saving:** ~$1-5/month from fewer unnecessary runs

---

## Weekly Cost Check Routine

**Every Friday, spend 5 minutes:**

1. Open **Cost Management → Cost Analysis**
2. View **Last 7 days** spending
3. Check if within expected range ($5-10/week)
4. Review **which resources** cost the most
5. Identify any anomalies (unexpected spikes)
6. Take action if needed (delete data, pause services)

**Example check:**
```
This week: $8.50
Breakdown:
- SQL Database: $3.50
- ADLS Storage: $2.00
- Synapse: $2.00
- ADF: $0.50
- Other: $0.50

Status: ✅ Within expected range
Action: None needed
```

---

## Cost Control Checklist

- [ ] Budget alert set to $100/month with 80% threshold
- [ ] Weekly cost review scheduled (every Friday)
- [ ] Synapse paused when not in use
- [ ] Old raw data deleted monthly
- [ ] Test data cleaned up after each session
- [ ] ADF triggers disabled during development
- [ ] Email notifications enabled for budget alerts

---

## Emergency Actions (If Cost Exceeds Budget)

**If monthly cost exceeds $100:**

1. **Immediate**: Pause Synapse workspace
2. **Immediate**: Delete all test/temp data from ADLS
3. **Within 24h**: Downsize SQL Database to Basic tier
4. **Within 24h**: Delete unnecessary resources (extra pipelines, linked services)
5. **Review**: Check Cost Analysis for unexpected charges

**Contact Microsoft Support** if charges seem incorrect.

---

## Cost Tracking Log

Use this table to track actual spending:

| Month | Week | Actual Cost | Budget | Notes |
|---|---|---|---|---|
| Mar 2026 | W1 (1-7) | $7.50 | $25 | Synapse paused 50% |
| Mar 2026 | W2 (8-14) | $8.20 | $25 | Deleted old raw data |
| Mar 2026 | W3 (15-21) | $9.10 | $25 | Full pipeline run |
| Mar 2026 | W4 (22-28) | $6.80 | $25 | Minimal activity |
| — | — | — | — | — |

---

## Key Takeaway

**"Pause, delete, downsize"** — whenever not actively using resources, pause or delete them. Azure is cheap when optimized, expensive when left running idle.

Keep cost monitoring as **part of your weekly routine**, not an afterthought.

---

**Last Updated**: March 30, 2026