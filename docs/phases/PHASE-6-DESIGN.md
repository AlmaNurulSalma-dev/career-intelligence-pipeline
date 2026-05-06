# Phase 6: ADF Data Flow Transformations — Design Document

**Date:** May 6, 2026  
**Author:** Alma  
**Status:** Design Phase (Ready for Implementation)

---

## 1. Objective

Transform raw scraped job listing data from multiple sources (Glints, JobStreet) into a standardized, cleaned dataset ready for downstream analytics and database loading.

**Scope:** Structural transformations only (normalization, standardization, deduplication)  
**Out of Scope:** Industry/job level categorization (defer to Phase 8 — Synapse Spark)

---

## 2. Data Sources

| Source | Format | Location | Frequency | Fields |
|--------|--------|----------|-----------|--------|
| **Glints** | JSON | `raw/glints/YYYY/MM/DD/` | Weekly (Mondays) | 11 fields |
| **JobStreet** | JSON | `raw/jobstreet/YYYY/MM/DD/` | Weekly (Mondays) | 8 fields |

### 2.1 Raw Data Structure

**Glints JSON Fields:**
```
job_id, title, company, location, salary, posted_date, job_url,
job_type, work_policy, experience_required, description
```

**JobStreet JSON Fields:**
```
job_id, title, company, location, job_type, salary, description, job_url
```

---

## 3. Data Quality Issues Identified

### 3.1 Missing/Null Values

| Field | Glints | JobStreet | Handling |
|-------|--------|-----------|----------|
| salary | "Not specified" (some) | "Not specified" (some) | Keep as-is (filter in Phase 8) |
| company | ✅ All present | "Not specified" (rare) | Keep, flag in downstream |
| job_type | ✅ All present | ✅ All present | Standardize format |
| experience_required | "Tidak Dicantumkan" / "Unknown" | ❌ Not present | Standardize to NULL |
| work_policy | ✅ All present | ❌ Not present | Standardize to NULL |
| posted_date | Varies ("X hari lalu") | ❌ Not present | Standardize to NULL |
| description | Sometimes "" (empty) | ✅ All present | Filter empty strings |

### 3.2 Inconsistent Formats

**Salary:**
- Glints: `"Rp 7 jt-20 jt"`
- JobStreet: `"Rp 8.000.000 – Rp 12.000.000 per month"`
- → **Need normalization to consistent format**

**Job Type:**
- Glints: Indonesian (`"Penuh Waktu"`, `"Kontrak"`, `"Magang"`)
- JobStreet: Indonesian/English mix (`"Full time"`, `"Kontrak/Temporer"`)
- → **Need standardization to English lowercase**

**Location:**
- Glints: `"Jakarta Selatan, DKI Jakarta"`
- JobStreet: `"Jakarta Utara, Jakarta Raya"`
- → **Need extraction of city name only, lowercase**

**Data Types:**
- All fields are STRING (no type conversion needed in ADF)
- Parsing to numbers deferred to Phase 7 (Synapse Spark)

### 3.3 Duplicate Detection

**Same-source duplicates:** Possible if scrapers run multiple times  
**Cross-source duplicates:** Same job posted on both Glints & JobStreet (common)

---

## 4. Design Decisions

### 4.1 Job ID Strategy: Composite Key (Option A) ✅

**Decision:** Create new composite ID combining source + original ID

```
composite_id = MD5(concat(source, original_job_id))

Example:
- Glints "3f20f6b8-9514-4fb7-a741-79a1e917e40d"
  → composite_id = MD5("glints3f20f6b8-9514-4fb7-a741-79a1e917e40d")
  → "a1b2c3d4e5f6..." (deterministic hash)

- JobStreet "91879616"
  → composite_id = MD5("jobstreet91879616")
  → "x9y8z7w6v5u4..." (different hash, different job)

- Same job from both sources gets DIFFERENT composite_id
  → Allows deduplication in Aggregate transformation
```

**Why this approach:**
- ✅ Preserves source info (trackable)
- ✅ Creates unique ID for each job record
- ✅ Deterministic (same input = same output, reproducible)
- ✅ Easy to debug (can regenerate)

---

### 4.2 Deduplication Strategy: Keep Most Recent (Option A) ✅

**Decision:** When same job exists across sources, keep the most recently posted version

```
Dedup Key: title + company + location (standardized)

Logic:
1. Group jobs by: title, company, location
2. For each group, keep: Record with MAX(posted_date)
3. Discard: All older duplicates

Example:
Glints:    "Data Engineer" + "PT X" + "jakarta" (posted 5 days ago)
JobStreet: "Data Engineer" + "PT X" + "jakarta" (posted 2 days ago)
→ KEEP: JobStreet record (more recent)
→ DISCARD: Glints record
```

**Why most recent:**
- ✅ Job postings get updated, re-posted with refined details
- ✅ Newer data = more accurate salary, requirements, etc.
- ✅ Prevents stale job listings from older postings

---

### 4.3 Scope: Exclude Categorization for Phase 6

**Decision:** Skip industry & job level categorization (defer to Phase 8)

**Rationale:**
- Phase 6 = structural transformations (normalize, standardize, deduplicate)
- Categorization = semantic analysis (better suited for Spark + NLP in Phase 8)
- Keeps Phase 6 focused, simpler pipeline
- Current data only covers Data/IT roles anyway

**Future:** Add in Phase 8 (Synapse Spark) once job descriptions are processed via NLP

---

## 5. Transformation Requirements

### 5.1 Transformations by Field

| Field | Input Format | Output Format | Transformation | Tool |
|-------|--------------|----------------|-----------------|------|
| **composite_id** | N/A (generate) | MD5 hash | MD5(concat(source, job_id)) | Derived Column |
| **source** | N/A (add) | "glints" or "jobstreet" | From file path | Select |
| **job_id** | Original ID | Keep original | Pass-through | Select |
| **title** | Mixed case | Lowercase, trimmed | `.lower().trim()` | Derived Column |
| **company** | Mixed case, "Not specified" | Lowercase, trimmed | `.lower().trim()` | Derived Column |
| **location** | "City, Province" | City only, lowercase | Extract + `.lower()` | Derived Column |
| **job_type** | Indonesian/English mix | English lowercase | Map + `.lower()` | Derived Column |
| **salary** | Multiple formats | Standardized string | Format to "Rp X.XXX.XXX-X.XXX.XXX" | Derived Column |
| **description** | Raw text | Trimmed | `.trim()`, remove empty | Filter |
| **posted_date** | "X hari lalu" or NULL | Standardized or NULL | Keep as-is (Glints) or NULL (JobStreet) | Select |
| **experience_required** | Indonesian text or NULL | As-is or NULL | Keep as-is (Glints) or NULL (JobStreet) | Select |
| **work_policy** | Indonesian text or NULL | As-is or NULL | Keep as-is (Glints) or NULL (JobStreet) | Select |
| **job_url** | Full URL | Full URL | Pass-through | Select |

### 5.2 Field Mapping Matrix

| Glints Field | JobStreet Field | Standardized Name | Comments |
|--------------|-----------------|-------------------|----------|
| job_id | job_id | job_id | Original ID, kept for reference |
| title | title | title | ✅ Direct match |
| company | company | company | ✅ Direct match |
| location | location | location | ✅ Direct match (needs normalization) |
| job_type | job_type | job_type | ✅ Direct match (needs standardization) |
| salary | salary | salary | ✅ Direct match (needs normalization) |
| description | description | description | ✅ Direct match |
| job_url | job_url | job_url | ✅ Direct match |
| posted_date | — | posted_date | Glints only, NULL for JobStreet |
| experience_required | — | experience_required | Glints only, NULL for JobStreet |
| work_policy | — | work_policy | Glints only, NULL for JobStreet |

---

## 6. Target Output Structure

**Output Location:** `transform/job-listings/YYYY/MM/DD/`  
**Format:** JSON (same structure as input, but cleaned)

```json
{
  "composite_id": "a1b2c3d4e5f6...",
  "source": "glints",
  "job_id": "3f20f6b8-9514-4fb7-a741-79a1e917e40d",
  "title": "data engineer",
  "company": "pt digital sejahtera nusantara",
  "location": "jakarta",
  "job_type": "full time",
  "salary": "Rp 7.000.000-20.000.000",
  "description": "Merancang, membangun, dan memelihara arsitektur data pipeline...",
  "posted_date": "16 hari yang lalu",
  "experience_required": "Tidak Dicantumkan",
  "work_policy": "Kerja di lokasi",
  "job_url": "https://glints.com/id/opportunities/..."
}
```

---

## 7. ADF Data Flow Architecture

### 7.1 Data Flow Steps

```
SOURCE (Glints JSON)
    ↓
[SELECT] → Pick all fields
    ↓
[DERIVED COLUMN] → Add: composite_id, source
    ↓
[DERIVED COLUMN] → Normalize: salary
    ↓
[DERIVED COLUMN] → Standardize: title, company, location, job_type
    ↓
[FILTER] → Remove empty descriptions
    ↓
[UNION] → Combine with JobStreet data
    ↓
[AGGREGATE] → Deduplicate by (title, company, location)
    ↓
[SELECT] → Reorder columns
    ↓
SINK (Transform layer ADLS)
```

### 7.2 Transformations Sequence

1. **Source - Glints**: Read JSON from `raw/glints/`
2. **Source - JobStreet**: Read JSON from `raw/jobstreet/`
3. **SELECT**: Pick relevant columns
4. **DERIVED COLUMN - Composite ID**: `MD5(concat(source, job_id))`
5. **DERIVED COLUMN - Salary Normalization**: Format to standard
6. **DERIVED COLUMN - Location Normalization**: Extract city, lowercase
7. **DERIVED COLUMN - Job Type Mapping**: Map to English, lowercase
8. **DERIVED COLUMN - Title/Company**: Trim and lowercase
9. **FILTER**: Remove rows where description is empty
10. **UNION**: Merge Glints + JobStreet streams
11. **AGGREGATE**: Group by (title, company, location), keep MAX(posted_date)
12. **SELECT**: Finalize column order
13. **SINK**: Write to `transform/job-listings/YYYY/MM/DD/`

---

## 8. Normalization Rules (Detailed)

See **DATA-TRANSFORMATION-SPEC.md** for detailed normalization rules per field.

---

## 9. Deduplication Rules (Detailed)

See **DEDUPLICATION-STRATEGY.md** for detailed dedup logic and examples.

---

## 10. Testing Strategy

### 10.1 Unit Testing (Per Transformation)

- [ ] Salary normalization: Test all formats (jt, full number, "Not specified")
- [ ] Location extraction: Test various province/city combinations
- [ ] Job type mapping: Test all values from both sources
- [ ] Title/company case conversion: Test mixed case, special chars
- [ ] Deduplication: Inject known duplicates, verify only 1 kept

### 10.2 Integration Testing

- [ ] Full pipeline: Sample 10 jobs from each source
- [ ] Verify output count after dedup (should be < input count)
- [ ] Validate all required fields present
- [ ] Check data types consistency

### 10.3 Sample Data Validation

- [ ] Run on `glints_sample_20260506.json`
- [ ] Run on `jobstreet_sample_20260506.json`
- [ ] Verify output in `transform/` folder
- [ ] Manually inspect 5-10 records

---

## 11. Prerequisites

- [ ] ADLS Gen 2 storage account: `sacareerintelligence`
- [ ] Containers: `raw`, `transform`
- [ ] Folders: `raw/glints/2026/05/06/`, `raw/jobstreet/2026/05/06/`
- [ ] Sample JSON files uploaded
- [ ] Azure Data Factory: `adf-career-intelligence`
- [ ] Linked Service to ADLS (already configured)

---

## 12. Next Steps

1. **Step 1:** Upload sample JSON to ADLS `raw/` folders
2. **Step 2:** Create ADF Data Flow for transformations
3. **Step 3:** Test on sample data
4. **Step 4:** Commit to GitHub (`[FEAT-10] Add ADF Data Flow transformations`)
5. **Step 5:** Scale up to full config (all locations, all job types)

---

## 13. References

- **Data Structure Analysis:** See DATA-TRANSFORMATION-SPEC.md
- **Deduplication Logic:** See DEDUPLICATION-STRATEGY.md
- **Glints Scraper:** `/scrapers/glints/glints_scraper.py`
- **JobStreet Scraper:** `/scrapers/jobstreet/jobstreet_scraper.py`
- **ADLS Architecture:** Medallion pattern (raw → transform → serve)

---

## 14. Document History

| Date | Version | Author | Changes |
|------|---------|--------|---------|
| 2026-05-06 | 1.0 | Alma | Initial design document |

---

**Status:** ✅ Design Complete, Ready for Implementation