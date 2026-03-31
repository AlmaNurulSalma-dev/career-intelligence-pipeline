# Career Intelligence Pipeline

A comprehensive Azure data engineering portfolio project that ingests job listings from multiple sources, analyzes skill gaps, and provides personalized career intelligence.

## Project Overview

- **Data Sources**: LinkedIn (CSV), Glints (scraping), JobStreet (scraping)
- **Ingestion Types**: CSV, JSON, Web Scraping
- **Data Collection**: Real-time daily scraping + weekly historical trend tracking
- **Transformations**: ADF Data Flow + Azure Synapse Spark
- **Storage**: ADLS Gen 2 + Azure SQL Database
- **Monitoring**: Azure Monitor + Logic Apps
- **Visualization**: Power BI Dashboard (6 views)
- **Version Control**: GitHub with feature branches

## Tech Stack

- **Orchestration**: Azure Data Factory
- **Storage**: Azure Data Lake Storage Gen 2
- **Transformations**: ADF Data Flow + Azure Synapse Analytics (Spark)
- **Database**: Azure SQL Database
- **Data Catalog**: Microsoft Purview
- **Visualization**: Power BI
- **Monitoring**: Azure Monitor + Logic Apps

## Project Structure
```
career-intelligence-pipeline/
├── docs/                    # Documentation & guides
│   ├── phases/             # Phase-by-phase execution docs
│   ├── architecture.md      # System architecture diagram
│   └── cost-monitoring.md   # Cost tracking & optimization
├── adf/                     # Azure Data Factory artifacts
│   ├── linkedservices/      # Data source connections
│   ├── pipelines/           # ADF pipeline definitions
│   ├── dataflows/           # Data Flow transformations
│   └── triggers/            # Schedule triggers
├── synapse/                 # Azure Synapse Spark
│   ├── notebooks/           # Interactive Jupyter notebooks
│   └── scripts/             # Reusable PySpark functions
├── sql/                     # Azure SQL Database
│   ├── schema/              # Table definitions
│   └── stored-procedures/   # SQL procedures
├── config/                  # Configuration files
│   └── pipeline-config.json # Pipeline settings
└── powerbi/                 # Power BI dashboards & reports
    ├── dashboards/
    └── reports/
```

## Getting Started

### Prerequisites
- Python 3.12+
- Git 2.43+
- Azure Account (pay-as-you-go subscription)
- GitHub Account with SSH key configured

### Phase-by-Phase Execution

1. **Phase 0**: Prerequisites & Environment Setup
2. **Phase 1**: GitHub Repository Setup
3. **Phase 2**: Azure Resource Provisioning
4. **Phase 3**: ADF & GitHub Integration
5. **Phase 4+**: Pipeline development & transformations

See `docs/phases/` for detailed step-by-step guides.

## Cost Monitoring

This project uses a pay-as-you-go Azure subscription. To minimize costs:
- Pause/delete resources when not in use
- Monitor spending regularly via Azure Cost Management
- See `docs/cost-monitoring.md` for detailed guidance

**Estimated monthly cost (optimized)**: ~$30-50

## Data Sources

| Source | Type | Ingestion Method | Frequency |
|---|---|---|---|
| LinkedIn Export | Skill Profile | Flat File CSV | Manual (monthly) |
| Config JSON | Preferences | Flat File JSON | Manual |
| Glints | Job Listings | Web Scraping | Daily (automated) |
| JobStreet | Job Listings | Web Scraping | Daily (automated) |
| Historical Data | Trends & Benchmarks | Self-collected | Accumulates weekly |

## Pipeline Outputs

- **ADLS Gen 2**: Raw & transformed data (partitioned by source & date)
- **Azure SQL Database**: 6 clean, queryable tables
- **Microsoft Purview**: Data catalog with lineage & PII labels
- **Power BI Dashboard**: 6 interactive views
- **Email Digest**: Automated weekly summary via Logic Apps

## Monitoring (6 Types)

1. Pipeline failure detection
2. Data quality checks
3. Performance monitoring
4. Data freshness alerts
5. Cost tracking
6. Business metric alerts

## Contributors

- **Alma** — Project Owner & Developer

## Status

**Current Phase**: Phase 0 - Prerequisites & Environment Setup

**Last Updated**: [Your current date]

---

*This portfolio project demonstrates end-to-end Azure data engineering skills including data ingestion, transformation, orchestration, monitoring, cataloging, and visualization.*