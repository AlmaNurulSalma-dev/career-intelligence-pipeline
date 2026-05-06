# Deduplication Strategy — Phase 6

**Date:** May 6, 2026  
**Author:** Alma  
**Purpose:** Define how to identify and remove duplicate job listings

---

## 1. Deduplication Overview

### 1.1 Problem Statement

When job listings are scraped from multiple sources (Glints, JobStreet), the same job posting may appear in both sources. Additionally, if scrapers run multiple times, jobs may be duplicated within the same source.

**Scenario 1: Cross-source duplicates (most common)**
```
Glints:    "Data Engineer" + "PT X" + "Jakarta" (posted 5 days ago)
JobStreet: "Data Engineer" + "PT X" + "Jakarta" (posted 2 days ago)
→ Same job, posted on both platforms, slightly different dates
→ Should keep only ONE (the more recent one)
```

**Scenario 2: Same-source duplicates (if scripts run multiple times)**
```
Glints Run 1: "Data Engineer" + "PT X" + "Jakarta"
Glints Run 2: "Data Engineer" + "PT X" + "Jakarta" (same data, run again)
→ Same job, from same scraper, duplicate entries
→ Should keep only ONE
```

### 1.2 Deduplication Decision: KEEP MOST RECENT ✅

**Strategy:** When duplicate jobs are identified, **keep the most recently posted version** and discard older ones.

**Rationale:**
- Job postings are updated, re-posted with refined details
- More recent posting = more accurate salary, requirements, responsibilities
- Prevents stale/outdated job information

---

## 2. Deduplication Key Definition

### 2.1 Composite Dedup Key

**Definition:**
```
Dedup Key = (title, company, location)

Where:
- title = job title (standardized: lowercase, trimmed)
- company = company name (standardized: lowercase, trimmed)
- location = city name (standardized: city only, lowercase)
```

**Reasoning:**
- These three fields uniquely identify a job posting across sources
- Same job, same company, same location = same job opening
- Other fields (salary, description, posted_date) may vary → use most recent

### 2.2 Why Not Use job_id?

❌ **job_id alone won't work:**
```
Glints job_id:    "3f20f6b8-9514-4fb7-a741-79a1e917e40d" (UUID)
JobStreet job_id: "91879616" (number)
→ Same job, different IDs (can't match)

Need to deduplicate BEFORE composite_id is generated,
using actual job attributes instead.
```

✅ **Use (title, company, location) instead:**
```
Both sources can be grouped by these standardized fields
Regardless of original job_id format
```

---

## 3. Deduplication Algorithm

### 3.1 Step-by-Step Logic

```
Step 1: Load all raw jobs (both sources combined)

Step 2: Standardize dedup key fields
  - Convert title to lowercase, trim
  - Convert company to lowercase, trim
  - Extract location (city only), lowercase
  - Remove direction suffixes (selatan, utara, etc.)

Step 3: Group jobs by composite key (title, company, location)

Step 4: For each group:
  - Count how many jobs in this group
  - If count = 1 → Keep as-is
  - If count > 1 → Keep ONLY the one with MAX(posted_date)
               → Discard all others

Step 5: Output deduplicated jobs
```

### 3.2 ADF Aggregate Transformation

In ADF Data Flow, this is implemented using the **AGGREGATE** transformation:

```
AGGREGATE Step:
  Group by: title, company, location
  
  Aggregate functions:
    - Keep: All fields from first record (or latest by timestamp)
    - Sort: by posted_date DESC (newest first)
    - Keep: Only first row per group
```

**ADF Expression:**
```
Group By:
  title
  company
  location

Then use Window function or ROW_NUMBER to select latest:
  rank() over(partition by title, company, location 
             order by posted_date desc) = 1
```

---

## 4. Deduplication Examples

### 4.1 Example 1: Exact Cross-Source Duplicate

**Input:**
```
Record 1 (Glints):
  job_id: "abc-123"
  source: "glints"
  title: "Data Engineer"
  company: "PT Maju Jaya"
  location: "Jakarta Selatan, DKI Jakarta"
  salary: "Rp 7 jt-20 jt"
  posted_date: "5 hari yang lalu"
  description: "Merancang pipeline data..."

Record 2 (JobStreet):
  job_id: "91879616"
  source: "jobstreet"
  title: "Data Engineer"
  company: "PT Maju Jaya"
  location: "Jakarta Selatan, Jakarta Raya"
  salary: "Rp 7.000.000-20.000.000"
  posted_date: "2 hari yang lalu"
  description: "Merancang pipeline data..."
```

**Standardized for dedup:**
```
Record 1: (title: "data engineer", company: "pt maju jaya", location: "jakarta")
Record 2: (title: "data engineer", company: "pt maju jaya", location: "jakarta")
→ SAME GROUP
```

**Dedup Decision:**
```
Group has 2 records
Post-dates: ["5 hari yang lalu", "2 hari yang lalu"]
Keep: Record 2 (JobStreet, more recent)
Discard: Record 1 (Glints, older)
```

**Output:**
```
Record 2 (JobStreet) is kept
Record 1 (Glints) is removed
Total records in group: 1
```

### 4.2 Example 2: Similar Jobs (NOT Duplicates)

**Input:**
```
Record 1:
  title: "Data Engineer" (Junior)
  company: "PT X"
  location: "jakarta"
  posted_date: "5 hari yang lalu"

Record 2:
  title: "Senior Data Engineer"
  company: "PT X"
  location: "jakarta"
  posted_date: "3 hari yang lalu"
```

**Standardized for dedup:**
```
Record 1: (title: "data engineer (junior)", company: "pt x", location: "jakarta")
Record 2: (title: "senior data engineer", company: "pt x", location: "jakarta")
→ DIFFERENT titles → DIFFERENT GROUPS
```

**Dedup Decision:**
```
Record 1 → Group 1 (only member) → KEEP
Record 2 → Group 2 (only member) → KEEP
Both records are kept (not duplicates, different titles)
```

### 4.3 Example 3: Same Job, Same Source (run twice)

**Input:**
```
Record 1 (Run 1):
  job_id: "abc-123"
  source: "glints"
  title: "Marketing Data Analyst"
  company: "PT Retail XYZ"
  location: "jakarta"
  posted_date: "12 hari yang lalu"

Record 2 (Run 2, same scraper):
  job_id: "abc-123"
  source: "glints"
  title: "Marketing Data Analyst"
  company: "PT Retail XYZ"
  location: "jakarta"
  posted_date: "12 hari yang lalu"
```

**Standardized:**
```
Record 1: (title: "marketing data analyst", company: "pt retail xyz", location: "jakarta")
Record 2: (title: "marketing data analyst", company: "pt retail xyz", location: "jakarta")
→ SAME GROUP
```

**Dedup Decision:**
```
Group has 2 records (identical)
Post-dates: ["12 hari yang lalu", "12 hari yang lalu"]
→ Same date, so keep first one (arbitrary)
Keep: Record 1
Discard: Record 2
Total: 1 record
```

### 4.4 Example 4: Job Reposted (newer version)

**Input:**
```
Record 1 (Old posting):
  job_id: "old-uuid"
  source: "glints"
  title: "Data Analyst"
  company: "PT Growth Analytics"
  location: "jakarta"
  posted_date: "30 hari yang lalu"
  salary: "Rp 5 jt-7 jt"
  description: "Outdated job description..."

Record 2 (Reposted, updated):
  job_id: "new-uuid"
  source: "glints"
  title: "Data Analyst"
  company: "PT Growth Analytics"
  location: "jakarta"
  posted_date: "3 hari yang lalu"
  salary: "Rp 6 jt-8 jt"
  description: "Updated job description with new benefits..."
```

**Standardized:**
```
Record 1: (title: "data analyst", company: "pt growth analytics", location: "jakarta")
Record 2: (title: "data analyst", company: "pt growth analytics", location: "jakarta")
→ SAME GROUP
```

**Dedup Decision:**
```
Group has 2 records
Post-dates: ["30 hari yang lalu", "3 hari yang lalu"]
→ Record 2 is newer (3 days ago vs 30 days ago)
Keep: Record 2 (updated posting with better salary)
Discard: Record 1 (old, outdated posting)
Total: 1 record (the newer one)
```

**Benefit:** Users see the most current job posting with updated details!

---

## 5. Edge Cases

### 5.1 Missing Data in Dedup Key

**Problem:** What if title, company, or location is missing/NULL?

```
Record 1:
  title: NULL
  company: "PT X"
  location: "jakarta"

Record 2:
  title: NULL
  company: "PT X"
  location: "jakarta"
```

**Solution:** **Filter out records with missing dedup key fields BEFORE aggregation**

```
In FILTER transformation:
Keep only rows where:
  - title is not NULL AND title != ""
  - company is not NULL AND company != "" AND company != "Not specified"
  - location is not NULL AND location != ""

Discard: Records with any NULL/empty dedup key field
```

### 5.2 Posted Date Missing or Same

**Problem:** If posted_date is NULL or both records have same date, which to keep?

```
Record 1:
  posted_date: "5 hari yang lalu"
  composite_id: "abc123"

Record 2:
  posted_date: "5 hari yang lalu" (or NULL)
  composite_id: "def456"
```

**Solution:** **Use composite_id as tiebreaker (keep first by ID order)**

```
In Aggregate:
Sort by:
  1. posted_date DESC (most recent first)
  2. composite_id ASC (alphabetical tiebreaker)

Keep: First record after sort
```

### 5.3 Multiple Jobs, Different Titles

**Problem:** What if one company has "Data Engineer" and "Senior Data Engineer" simultaneously?

```
Record 1: "Data Engineer" + "PT X" + "jakarta"
Record 2: "Senior Data Engineer" + "PT X" + "jakarta"
```

**Solution:** **Both are kept (different dedup key groups)**

```
Group 1: (title: "data engineer", company: "pt x", location: "jakarta")
  → Only Record 1 → Keep

Group 2: (title: "senior data engineer", company: "pt x", location: "jakarta")
  → Only Record 2 → Keep

Output: 2 records (both kept, different positions)
```

---

## 6. Deduplication Impact on Data

### 6.1 Expected Reduction

**Before dedup (sample data):**
```
Glints:    10 jobs
JobStreet: 10 jobs
Total:     20 jobs
```

**After dedup (estimated with 40% cross-source overlap):**
```
Unique jobs:    12 jobs
Removed:        8 jobs (40% reduction)
```

**Why 40% estimate?**
- Same job often posted on both platforms
- Job descriptions similar across sources
- Companies use multiple channels

### 6.2 Data Quality Improvement

✅ **Benefits of deduplication:**
- Eliminates redundant records
- Ensures database doesn't have duplicates
- Reduces storage cost
- Improves query performance (fewer rows)
- User sees each job only once

❌ **Potential risks (mitigated):**
- Loss of source information → Mitigated: Keep source + job_id fields
- Losing older posting details → Mitigated: Keep most recent (usually better)
- Missing edge cases → Mitigated: Extensive testing before production

---

## 7. ADF Implementation

### 7.1 Aggregate Transformation Settings

```
Transformation: AGGREGATE

Input: All records (Glints + JobStreet combined via UNION)

Aggregate Settings:
  Group by:
    - title
    - company
    - location
  
  Aggregates:
    - Max of posted_date (or latest composite_id)
    
  Keep all other columns:
    - job_id
    - composite_id
    - source
    - salary
    - description
    - etc.
  
  Sort:
    - posted_date DESC (newest first)
    
  Output: Only first record per group
```

### 7.2 Alternative: Window Function (if Aggregate not available)

```
Transformation: Derived Column

Add column:
  row_num = row_number() over (
    partition by title, company, location
    order by posted_date desc, composite_id asc
  )

Then FILTER:
  Keep only rows where row_num = 1
```

---

## 8. Testing Deduplication

### 8.1 Test Case 1: Known Duplicates

**Inject test data:**
```
Add 2 identical job records (same title, company, location)
Run dedup
Verify: Only 1 record in output
```

### 8.2 Test Case 2: Cross-Source Duplicates

**Inject test data:**
```
Add same job from Glints and JobStreet
Run dedup
Verify: Only 1 record (the more recent one)
```

### 8.3 Test Case 3: Different Jobs (NOT duplicates)

**Inject test data:**
```
Add "Data Engineer" + "PT X" + "Jakarta"
Add "Senior Data Engineer" + "PT X" + "Jakarta"
Run dedup
Verify: Both records kept (different titles)
```

### 8.4 Test Case 4: Reposted Job

**Inject test data:**
```
Add old posting: posted 30 days ago
Add new posting: posted 2 days ago (same job, updated salary)
Run dedup
Verify: Only new posting kept (with updated salary)
```

---

## 9. Sample SQL for Validation (Post-ADF)

After data is loaded to SQL, verify deduplication with:

```sql
-- Check for any remaining duplicates
SELECT 
  title, company, location, 
  COUNT(*) as duplicate_count
FROM job_listings
GROUP BY title, company, location
HAVING COUNT(*) > 1
ORDER BY duplicate_count DESC;

-- Expected result: Empty (0 rows)
-- If any rows appear, dedup failed
```

---

## 10. Document History

| Date | Version | Author | Changes |
|------|---------|--------|---------|
| 2026-05-06 | 1.0 | Alma | Initial deduplication strategy |

---

**Status:** ✅ Deduplication Strategy Complete, Ready for ADF Implementation