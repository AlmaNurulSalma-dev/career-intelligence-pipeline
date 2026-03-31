# Phase 0: Prerequisites & Environment Setup

## Phase Overview

Phase 0 adalah foundational step — memastikan semua tools, accounts, dan local setup ready sebelum Phase 1 (GitHub repo setup) dan Phase 2 (Azure resources).

**Status**: ✅ COMPLETE

**Duration**: ~2-3 hours (one-time setup)

---

## Completed Steps

### ✅ Step 1: Audit Local Tools

**Objective:** Verify Python, Git, and Azure CLI installed

| Tool | Version | Status | Purpose |
|---|---|---|---|
| Python | 3.12.3 | ✅ Installed | For PySpark scripts, data processing |
| Git | 2.43.0 | ✅ Installed | Version control, GitHub integration |
| Azure CLI | Latest | ✅ Installed | Authentication to Azure (az login only) |

**Verification commands run:**
```powershell
python3 --version      # Output: Python 3.12.3
git --version          # Output: git version 2.43.0
az --version           # Output: [Version info]
```

---

### ✅ Step 2: SSH Key Setup for GitHub

**Objective:** Create SSH key pair and authenticate with GitHub

**Actions completed:**

1. **Generated SSH key pair:**
   - Command: `ssh-keygen -t ed25519 -C "almanurulsalma@gmail.com"`
   - Location: `C:\Users\kinet\OneDrive\Documents\PROJECT-ALMAAA\career-intelligence-pipeline\`
   - Files created:
     - `id_ed25519` (private key — NEVER commit)
     - `id_ed25519.pub` (public key — added to GitHub)

2. **Added public key to GitHub:**
   - GitHub Settings → SSH and GPG keys → New SSH key
   - Title: `Career Intelligence Pipeline - Alma`
   - Key type: Authentication Key
   - Pasted: Content of `id_ed25519.pub`

3. **Started SSH agent:**
```powershell
   Get-Service ssh-agent | Set-Service -StartupType Automatic
   Start-Service ssh-agent
   ssh-add "C:\Users\kinet\OneDrive\Documents\PROJECT-ALMAAA\career-intelligence-pipeline\id_ed25519"
```

4. **Verified SSH connection:**
```powershell
   ssh -T git@github.com
```
   Output: `Hi <username>! You've successfully authenticated...` ✅

**Result:** SSH authentication to GitHub working. Ready for Phase 1 (GitHub repo operations).

---

### ✅ Step 3: Local Project Folder Structure

**Objective:** Create organized folder hierarchy for all project artifacts

**Folders created:**
```
career-intelligence-pipeline/
├── docs/
│   ├── phases/           (Phase documentation)
│   ├── architecture.md   (System design)
│   └── cost-monitoring.md (Cost tracking guide)
├── adf/
│   ├── linkedservices/   (Data source configs)
│   ├── pipelines/        (ADF pipeline JSONs)
│   ├── dataflows/        (Data Flow definitions)
│   └── triggers/         (Schedule triggers)
├── synapse/
│   ├── notebooks/        (PySpark Jupyter notebooks)
│   └── scripts/          (Reusable PySpark functions)
├── sql/
│   ├── schema/           (Table DDL scripts)
│   └── stored-procedures/(SQL procedures)
├── config/
│   └── pipeline-config.json
├── powerbi/
│   ├── dashboards/       (Power BI dashboard files)
│   └── reports/          (Power BI reports)
└── id_ed25519*           (SSH keys — in .gitignore)
```

**Purpose of each folder:**
- `docs/` — All documentation (guides, architecture, cost tracking)
- `adf/` — Azure Data Factory artifact definitions (linked services, pipelines, data flows)
- `synapse/` — Azure Synapse Spark code (notebooks for interactive dev, scripts for production code)
- `sql/` — SQL Database scripts (table schemas, stored procedures for upserts)
- `config/` — Configuration files (pipeline settings, resource names)
- `powerbi/` — Power BI dashboard definitions & reports

---

### ✅ Step 4: Initialize Documentation

**Objective:** Create initial documentation templates

**Files created:**

| File | Purpose | Status |
|---|---|---|
| `.gitignore` | Define which files NOT to commit (passwords, keys, cache) | ✅ Created |
| `README.md` | Main project documentation (overview, tech stack, getting started) | ✅ Created |
| `docs/architecture.md` | High-level system design (data flow, components, monitoring) | ✅ Created |
| `docs/cost-monitoring.md` | Cost tracking & optimization strategies | ✅ Created |
| `docs/phases/phase0-prerequisites.md` | This file — Phase 0 completion docs | ✅ Creating |

**Key content in .gitignore:**
```
# SENSITIVE — Never commit:
secrets.json           (passwords, API keys)
id_ed25519            (private SSH key)
*.pem                 (private certificates)

# AUTO-GENERATED — Don't commit:
__pycache__/          (Python bytecode)
*.pyc, *.pyo          (Compiled Python)
venv/                 (Virtual environment)

# LOCAL-ONLY — Don't commit:
.env                  (Local environment variables)
.vscode/              (IDE settings)
*.log                 (Log files)
```

### ✅ Step 5: Data Sources & Scraping Strategy Finalized

**Objective:** Define final data sources and scraping approach

**Final Data Sources (5 Total):**

| # | Source | Type | Ingestion Method | Frequency | Status |
|---|---|---|---|---|---|
| 1 | LinkedIn CSV | Skill Profile | Flat File CSV | Manual monthly | ✅ Configured |
| 2 | Config JSON | Preferences | Flat File JSON | Manual | ✅ Configured |
| 3 | Glints | Job Listings | Web Scraping (Selenium) | Daily 02:00 UTC+7 | ✅ Configured |
| 4 | JobStreet | Job Listings | Web Scraping (Selenium) | Daily 03:00 UTC+7 | ✅ Configured |
| 5 | Historical Data | Trends & Benchmarks | Self-collected weekly | Weekly (Mondays) | ✅ Configured |

**Scraping Implementation Details:**

*Why Selenium (not BeautifulSoup)?*
- Both Glints & JobStreet use JavaScript for dynamic data loading
- BeautifulSoup gets empty HTML (before JS executes)
- Selenium loads full browser, waits for JS, gets complete data
- Selenium required for modern web apps

*Anti-Scraping Measures (Robustness):*
- Rotating proxies: Different IP per request (avoid IP blocking)
- User-agent rotation: Different browser identity per request
- Random delays: 2-5 seconds between requests (look human, respect rate limits)
- JavaScript rendering: Wait for dynamic content to load
- Error handling: Retry logic (3 attempts, 10-second delay)
- Monitoring: Track scraper health, alert on failures

*Historical Data Collection Strategy:*
- Week 1: Baseline scrape (Glints + JobStreet)
- Week 2: Scrape again, compare skill frequencies
- Week 3: Scrape again, calculate trends
- Week 4+: Continue accumulating, trends become accurate over time
- Data points tracked: Skill frequency, salary ranges, company patterns, job titles
- Retention: Permanent (never delete historical data)

**Configuration Stored In:**
- `config/pipeline-config.json` — Detailed scraping configs, endpoints, parameters
- `config/proxies.txt` — Proxy list (to be created during Phase 3)
- `config/user_agents.txt` — Browser user agents (to be created during Phase 3)

**Next Actions (Phase 3+):**
- Develop Python Selenium scrapers for Glints & JobStreet
- Test scraping locally before Azure integration
- Implement retry logic & error handling
- Setup proxy rotation & user-agent lists
- Integrate scrapers into ADF pipelines

---

## Prerequisites Checklist

- [x] Python 3.12.3 installed & verified
- [x] Git 2.43.0 installed & verified
- [x] Azure CLI installed & verified (authentication only)
- [x] SSH key pair generated
- [x] Public key added to GitHub
- [x] SSH authentication verified (`ssh -T git@github.com`)
- [x] Local project folder created: `C:\Users\kinet\OneDrive\Documents\PROJECT-ALMAAA\career-intelligence-pipeline`
- [x] Folder structure initialized (docs/, adf/, synapse/, sql/, config/, powerbi/)
- [x] Initial documentation created (.gitignore, README.md, architecture.md, cost-monitoring.md)
- [x] Git configured for SSH key usage
- [x] Data sources finalized (Glints + JobStreet web scraping)
- [x] Scraping strategy defined (Selenium + anti-scraping measures)
- [x] Historical data collection plan documented
- [x] config/pipeline-config.json created with scraping configs

---

---

## Phase 0 Summary

**What we've accomplished:**
✅ Local environment setup (Python, Git, Azure CLI)
✅ SSH authentication configured
✅ Project folder structure created
✅ Documentation templates initialized
✅ Data sources & scraping strategy finalized
✅ Configuration management planned

**Key decisions made:**
- Use Selenium for robust web scraping (JavaScript rendering)
- Scrape Glints & JobStreet (skip LinkedIn due to restrictions)
- Collect historical data weekly for trend analysis
- Implement anti-scraping measures (proxies, delays, user-agent rotation)

---

## Next Steps (Phase 1)

**Phase 1: GitHub Repository Setup**

Now that local environment & strategy are ready:

1. Initialize Git repository locally (`git init`)
2. Add all files to Git (`git add .`)
3. Create first commit (`git commit -m "[CHORE-01] Initialize project structure and strategy"`)
4. Create GitHub repository `career-intelligence-pipeline`
5. Configure remote (`git remote add origin git@github.com:alma-dataengineer/career-intelligence-pipeline.git`)
6. Push to GitHub (`git push -u origin main`)
7. Verify repository on GitHub
8. Create `main` branch protection rules (require PRs)

**Estimated duration:** ~30 minutes

**Phase 1 Deliverables:**
- GitHub repository created & synced
- Initial commit with full Phase 0 documentation
- Branch protection configured
- Ready for Phase 2 (Azure resources)

---

## Cost Impact (Phase 0)

**Cost**: $0 (no Azure resources created yet)

All work in Phase 0 is local machine only:
- SSH keys: Local only
- Git config: Local only
- Folders & files: Local storage only

Azure charges begin in **Phase 2** (resource provisioning).

---

## Key Learnings (Phase 0)

1. **SSH authentication** — Secure, password-less GitHub operations
2. **Project structure** — Organized folder hierarchy for complex data project
3. **Documentation-first** — Start with architecture & cost planning before coding
4. **.gitignore importance** — Prevent accidental commit of secrets
5. **Cost awareness** — Document cost tracking from day 1

---

## Troubleshooting (Phase 0)

**Issue: SSH connection to GitHub failed**
- Solution: Verify SSH agent running, key added with `ssh-add`, public key on GitHub settings

**Issue: Folder structure creation failed**
- Solution: Ensure OneDrive folder path exists, create manually via PowerShell or File Explorer

**Issue: .gitignore not working**
- Solution: Files tracked before .gitignore created won't be ignored. Use `git rm --cached <file>` to untrack.

---

## Phase 0 Complete! ✅

All prerequisites ready. Ready to move to **Phase 1: GitHub Repository Setup**.

---

**Phase Status**: COMPLETE  
**Next Phase**: Phase 1 (GitHub Repository Setup)  
**Last Updated**: March 30, 2026  
**Owner**: Alma