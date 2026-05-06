# Data Transformation Specification — Phase 6

**Date:** May 6, 2026  
**Author:** Alma  
**Purpose:** Detailed normalization rules for each field in ADF Data Flow

---

## 1. Salary Normalization

### 1.1 Problem Statement

Salary data comes in multiple formats:

```
Glints Format 1:     "Rp 7 jt-20 jt"
Glints Format 2:     "Rp 5,5 jt-7 jt"
Glints Format 3:     "Rp 600 rb-1 jt"
Glints Format 4:     "Not specified"

JobStreet Format 1:  "Rp 5.000.000 – Rp 5.500.000 per month"
JobStreet Format 2:  "Rp 8.000.000 – Rp 12.000.000 per month"
JobStreet Format 3:  "Not specified"
```

### 1.2 Target Format

```
Standardized Output: "Rp X.XXX.XXX-X.XXX.XXX"

Examples:
- Input: "Rp 7 jt-20 jt"
  Output: "Rp 7.000.000-20.000.000"

- Input: "Rp 5,5 jt-7 jt"
  Output: "Rp 5.500.000-7.000.000"

- Input: "Rp 600 rb-1 jt"
  Output: "Rp 600.000-1.000.000"

- Input: "Rp 5.000.000 – Rp 5.500.000 per month"
  Output: "Rp 5.000.000-5.500.000"

- Input: "Not specified"
  Output: "Not specified" (pass-through)
```

### 1.3 Normalization Rules

**Step 1: Check if "Not specified"**
```
IF salary contains "Not specified" → Output "Not specified"
ELSE → Continue to Step 2
```

**Step 2: Extract numbers and scale factor**

| Pattern | Scale | Example |
|---------|-------|---------|
| Contains "jt" | × 1,000,000 | "7 jt" → 7,000,000 |
| Contains "rb" | × 1,000 | "600 rb" → 600,000 |
| Contains "." | × 1 | "5.000.000" → 5,000,000 |

**Step 3: Parse min and max values**
```
- Remove currency ("Rp")
- Remove month reference ("per month")
- Split by "-" or "–" or "hingga"
- Extract left number (min) and right number (max)
- Apply scale factor to each

Example 1: "Rp 7 jt-20 jt"
  → Split: ["7 jt", "20 jt"]
  → Scale: [7*1M, 20*1M] = [7000000, 20000000]
  → Format: "Rp 7.000.000-20.000.000"

Example 2: "Rp 5,5 jt-7 jt"
  → Split: ["5,5 jt", "7 jt"]
  → Scale: [5.5*1M, 7*1M] = [5500000, 7000000]
  → Format: "Rp 5.500.000-7.000.000"

Example 3: "Rp 5.000.000 – Rp 5.500.000 per month"
  → Remove "Rp", "per month"
  → Split: ["5.000.000", "5.500.000"]
  → Scale: [5000000, 5500000]
  → Format: "Rp 5.000.000-5.500.000"
```

**Step 4: Format with thousands separator**
```
- Add thousands separator (period every 3 digits from right)
- Add "Rp " prefix
- Join with "-"

Example: [7000000, 20000000] → "Rp 7.000.000-20.000.000"
```

### 1.4 ADF Derived Column Expression

```
iif(
  contains(salary, 'Not specified'),
  'Not specified',
  /* Extract and normalize */
  'Rp ' + 
  /* This is pseudocode; actual ADF syntax in next section */
)
```

### 1.5 Why Keep as String in ADF?

- Salary has mixed currency references ("jt", "rb", full number)
- Parsing logic is complex, better in Spark
- ADF is good for structural transformations
- Will convert to numbers in Phase 7 (Synapse Spark) for analysis

**In Phase 7:** Parse to `salary_min` and `salary_max` (numbers) for benchmarking

---

## 2. Job Type Standardization

### 2.1 Problem Statement

Job types come in Indonesian or mixed Indonesian/English:

```
Glints Values:
- "Penuh Waktu" (Full time)
- "Kontrak" (Contract)
- "Paruh Waktu" (Part time)
- "Magang" (Internship)
- "Freelance" (Freelance)

JobStreet Values:
- "Full time"
- "Paruh waktu" (Part time)
- "Kontrak/Temporer" (Contract/Temporary)
- "Kasual/Liburan" (Casual/Holiday)
```

### 2.2 Target Values

Standardize to **English, lowercase**:

```
full time
part time
contract
internship
freelance
casual
```

### 2.3 Mapping Rules

| Input | Output | Source |
|-------|--------|--------|
| "Penuh Waktu" | "full time" | Glints |
| "Full time" | "full time" | JobStreet |
| "Paruh Waktu" | "part time" | Glints |
| "paruh waktu" | "part time" | JobStreet |
| "Kontrak" | "contract" | Glints |
| "Kontrak/Temporer" | "contract" | JobStreet |
| "Magang" | "internship" | Glints |
| "Freelance" | "freelance" | Glints |
| "Kasual/Liburan" | "casual" | JobStreet |
| "Unknown" | "unknown" | (fallback) |

### 2.4 ADF Derived Column Expression

```
lower(
  iif(contains(lower(job_type), 'penuh') || contains(lower(job_type), 'full'),
    'full time',
  iif(contains(lower(job_type), 'paruh'),
    'part time',
  iif(contains(lower(job_type), 'kontrak'),
    'contract',
  iif(contains(lower(job_type), 'magang'),
    'internship',
  iif(contains(lower(job_type), 'freelance'),
    'freelance',
  iif(contains(lower(job_type), 'kasual'),
    'casual',
    'unknown'
  ))))))
)
```

### 2.5 Testing Examples

```
Input: "Penuh Waktu" → Output: "full time" ✅
Input: "Full time" → Output: "full time" ✅
Input: "Kontrak/Temporer" → Output: "contract" ✅
Input: "Paruh Waktu" → Output: "part time" ✅
Input: "Magang" → Output: "internship" ✅
Input: "Kasual/Liburan" → Output: "casual" ✅
```

---

## 3. Location Normalization

### 3.1 Problem Statement

Locations include city and province, sometimes with prefix:

```
"Jakarta Selatan, DKI Jakarta"
"Jakarta Pusat, DKI Jakarta"
"Bekasi Utara, Jawa Barat"
"Bogor, Jawa Barat"
"Tangerang Selatan, Banten"
"Jakarta Raya" (inconsistent naming)
"Cakung, Jakarta Raya"
"Cibitung, Jawa Barat"
"Kabupaten Bekasi, Jawa Barat"
"Kota Bekasi" (with prefix)
```

### 3.2 Target Format

**City name only, lowercase**:

```
jakarta
bekasi
bogor
tangerang
bandung
surabaya
etc.
```

### 3.3 Normalization Rules

**Step 1: Lowercase everything**
```
"Jakarta Selatan, DKI Jakarta" → "jakarta selatan, dki jakarta"
```

**Step 2: Extract city (before comma)**
```
Split by ","
Take first part: "jakarta selatan"
```

**Step 3: Extract main city name**
```
Remove sub-districts like "selatan", "pusat", "utara", "barat", "timur"
"jakarta selatan" → "jakarta"
"bekasi utara" → "bekasi"
"tangerang selatan" → "tangerang"
```

**Step 4: Handle special cases**
```
"jakarta raya" → "jakarta"
"kota bekasi" / "kabupaten bekasi" → "bekasi"
"dki jakarta" → "jakarta"
"jawa barat" → (remove, not needed)
```

**Step 5: Trim and finalize**
```
Final output: "jakarta", "bekasi", "bogor", "tangerang"
```

### 3.4 ADF Derived Column Expression

```
lower(
  trim(
    case
      when contains(location, ',') then substring(location, 1, indexOf(location, ',') - 1)
      else location
    end
  )
)
/* Then remove direction suffixes */
replace(replace(replace(replace(
  [above_result],
  ' selatan', ''),
  ' utara', ''),
  ' barat', ''),
  ' timur', '')
```

### 3.5 City Mapping (Optional, if needed)

If you want to standardize "Jakarta Raya", "DKI Jakarta" to single "Jakarta":

```
"jakarta selatan" → "jakarta"
"jakarta pusat" → "jakarta"
"jakarta utara" → "jakarta"
"jakarta timur" → "jakarta"
"jakarta raya" → "jakarta"
"dki jakarta" → "jakarta"

"bekasi" → "bekasi"
"kabupaten bekasi" → "bekasi"
"bekasi utara" → "bekasi"

"tangerang" → "tangerang"
"tangerang selatan" → "tangerang"
"kota tangerang" → "tangerang"

etc.
```

### 3.6 Testing Examples

```
Input: "Jakarta Selatan, DKI Jakarta" → Output: "jakarta" ✅
Input: "Bekasi Utara, Jawa Barat" → Output: "bekasi" ✅
Input: "Cakung, Jakarta Raya" → Output: "jakarta" (after cleaning) ✅
Input: "Bogor, Jawa Barat" → Output: "bogor" ✅
```

---

## 4. Title & Company Standardization

### 4.1 Problem Statement

Titles and companies come in mixed case:

```
"Data Analyst/Data Scientist/Data Engineer/AI Engineer"
"PT DIGITAL SEJAHTERA NUSANTARA"
"ADI Consulting"
"Nadeem Indonesia"
"Insan Halal Cendekia"
```

### 4.2 Target Format

**Lowercase, trimmed**:

```
"data analyst/data scientist/data engineer/ai engineer"
"pt digital sejahtera nusantara"
"adi consulting"
"nadeem indonesia"
"insan halal cendekia"
```

### 4.3 Normalization Rules

**Step 1: Convert to lowercase**
```
lower(title)
lower(company)
```

**Step 2: Trim whitespace**
```
trim(lower(title))
trim(lower(company))
```

### 4.4 ADF Derived Column Expression

```
/* For Title */
trim(lower(title))

/* For Company */
trim(lower(company))
```

### 4.5 Why Lowercase?

- Consistency across sources
- Easier for downstream joins/matching
- Reduces duplicate keys (e.g., "Data Engineer" vs "data engineer")
- Can reverse case conversion in Power BI if needed for reports

---

## 5. Composite ID Generation

### 5.1 Problem Statement

Need a unique identifier that:
- Combines source + original job_id
- Is deterministic (reproducible)
- Preserves source info for debugging

```
Glints job_id:    "3f20f6b8-9514-4fb7-a741-79a1e917e40d" (UUID)
JobStreet job_id: "91879616" (number)
→ Different formats, need unified key
```

### 5.2 Solution: MD5 Hash

**Formula:**
```
composite_id = MD5(concat(source, original_job_id))

Where:
- source = "glints" or "jobstreet" (added in SELECT step)
- original_job_id = original job_id value
```

**Example:**
```
Glints job:
  source = "glints"
  job_id = "3f20f6b8-9514-4fb7-a741-79a1e917e40d"
  → concat: "glints3f20f6b8-9514-4fb7-a741-79a1e917e40d"
  → MD5: "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6"

JobStreet job:
  source = "jobstreet"
  job_id = "91879616"
  → concat: "jobstreet91879616"
  → MD5: "x9y8z7w6v5u4t3s2r1q0p9o8n7m6l5k4"

Different inputs → Different outputs (good for dedup!)
```

### 5.3 ADF Derived Column Expression

```
md5(concat(source, job_id))
```

**Note:** ADF has built-in `md5()` function. If not available, use:
```
/* Alternative: Use source + job_id as composite key directly */
concat(source, '_', job_id)
```

### 5.4 Why MD5?

- Deterministic (same input always produces same hash)
- Compact (32 characters)
- Collision-free for practical purposes
- Reversible if needed (store original_job_id separately)

---

## 6. Description Field Handling

### 6.1 Problem Statement

Description field can be:
- Long text (hundreds of words)
- Empty string ("")
- NULL

```
Glints: Usually present, detailed
JobStreet: Usually present, shorter
Empty descriptions: Should be filtered out
```

### 6.2 Target Format

**Keep as-is, but filter out empty ones**:

```
- Trim whitespace
- Remove completely empty descriptions
- Keep valid descriptions as-is (don't modify content)
```

### 6.3 Handling in ADF

**In SELECT step:**
```
Trim description: trim(description)
```

**In FILTER step:**
```
Keep only rows where: length(trim(description)) > 0
```

### 6.4 Why Not Truncate?

- Full description needed for Phase 7 (NLP processing)
- Truncation loses context
- Can truncate in Phase 8+ if needed for display

---

## 7. Posted Date Field Handling

### 7.1 Problem Statement

Posted date comes in different formats:

```
Glints:    "16 hari yang lalu" (relative time in Indonesian)
JobStreet: NULL / not available
```

### 7.2 Target Format

**Keep as-is for now**:

```
Glints: Keep original string "16 hari yang lalu"
JobStreet: NULL
```

### 7.3 Why Not Normalize to Absolute Date?

- Relative dates ("16 hari yang lalu") are hard to parse without context
- Would need current date reference
- Can convert to absolute dates in Phase 7 (Synapse) if needed
- For now, keep as informational field

### 7.4 ADF Handling

```
SELECT: posted_date (pass-through as-is)
```

---

## 8. Experience Required Field Handling

### 8.1 Problem Statement

Experience field only in Glints:

```
Glints:    "1 - 3 tahun", "Tidak Dicantumkan", "Fresh graduate", etc.
JobStreet: NULL (not available)
```

### 8.2 Target Format

**Keep as-is for now**:

```
Glints: Keep original value
JobStreet: NULL
```

### 8.3 Why Not Extract Job Level?

- Categorization deferred to Phase 8
- JobStreet doesn't have this field
- Can extract/map in Phase 8 when full context available

### 8.4 ADF Handling

```
SELECT: experience_required (pass-through as-is)
```

---

## 9. Work Policy Field Handling

### 9.1 Problem Statement

Work policy only in Glints:

```
Glints:    "Kerja di lokasi" (on-site), "Remote", etc.
JobStreet: NULL (not available)
```

### 9.2 Target Format

**Keep as-is for now**:

```
Glints: Keep original value
JobStreet: NULL
```

### 9.3 ADF Handling

```
SELECT: work_policy (pass-through as-is)
```

---

## 10. Field Summary Table

| Field | Glints Format | JobStreet Format | Transformation | Output Format |
|-------|---------------|------------------|-----------------|----------------|
| composite_id | - | - | Generate MD5(source + job_id) | "a1b2c3d4..." |
| source | - | - | Add value | "glints" / "jobstreet" |
| job_id | UUID | Number | Pass-through | Original value |
| title | Mixed case | Mixed case | Lowercase, trim | "data engineer" |
| company | Mixed case | Mixed case / "Not specified" | Lowercase, trim | "pt x" |
| location | "City, Province" | "City, Province" | Extract city, lowercase | "jakarta" |
| job_type | Indonesian | Indonesian/English | Map to English, lowercase | "full time" |
| salary | "Rp X jt-X jt" | "Rp X.XXX.XXX – Rp X.XXX.XXX" | Normalize format | "Rp X.XXX.XXX-X.XXX.XXX" |
| description | Text / "" | Text | Trim, filter empty | Text or filtered out |
| posted_date | "X hari lalu" | NULL | Pass-through | "16 hari yang lalu" / NULL |
| experience_required | Text / "Tidak Dicantumkan" | NULL | Pass-through | Text / NULL |
| work_policy | Text | NULL | Pass-through | Text / NULL |
| job_url | Full URL | Full URL | Pass-through | Full URL |

---

## 11. Testing Checklist

- [ ] Salary: Test all 6 formats (jt, rb, full number, comma, "Not specified")
- [ ] Job Type: Test all 6 values from both sources
- [ ] Location: Test compound locations (Jakarta Selatan, Kabupaten, etc.)
- [ ] Title/Company: Test mixed case, special characters, accents
- [ ] Composite ID: Verify MD5 is deterministic (run twice, get same hash)
- [ ] Filter: Verify empty descriptions are removed
- [ ] Union: Verify both sources merge correctly

---

## 12. Document History

| Date | Version | Author | Changes |
|------|---------|--------|---------|
| 2026-05-06 | 1.0 | Alma | Initial transformation spec |

---

**Status:** ✅ Specification Complete, Ready for ADF Implementation