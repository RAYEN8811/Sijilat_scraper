# Bahrain Sijilat Commercial Registration Scraper Prototype

**Author / Candidate Submission for Frederic**  
**Target Entity Selected:** BAPCO REFINING B.S.C CLOSED (CR Number: `48602`, Branch: `1` of `13`)  
**Portal:** Kingdom of Bahrain – Ministry of Industry and Commerce (MOIC) – Sijilat Public Registry (`https://www.sijilat.bh`)  
**Time Spent:** Approximately 70 minutes (well within the 2-hour limit)  
**Execution Environment:** Standard Python 3.8+ (Zero external pip dependencies required)

---

## 1. Quick Start & Execution

### Dependencies
This prototype uses **Python standard libraries exclusively** (`urllib.request`, `urllib.parse`, `hmac`, `hashlib`, `json`, `datetime`, `argparse`, `time`). No third-party packages or virtual environment installations are required.

### Commands to Run

#### 1. Primary Live Extraction (Target Selected Business: CR `48602`, Branch `1`)
```bash
python sijilat_scraper.py --cr 48602 --output output/cr_48602_run1.json
```

#### 2. Repeat Run (Demonstrating Idempotency / Deterministic Collection)
```bash
python sijilat_scraper.py --cr 48602 --output output/cr_48602_run2.json
```

#### 3. All Branches Extraction (Extracting all 13 branches of CR `48602`)
```bash
python sijilat_scraper.py --cr 48602 --all-branches --output output/cr_48602_all_branches.json
```

#### 4. Live Negative / Not Found Case (Non-existent CR `999999999`)
```bash
python sijilat_scraper.py --cr 999999999 --output output/cr_999999999_not_found.json
```

#### 5. Simulated Failure / Incomplete-Data Case (Explicitly Labeled)
```bash
python sijilat_scraper.py --cr 48602 --simulate-failure --output output/cr_48602_simulated_failure.json
```

#### 6. Run the Automated Test Suite
```bash
python -m unittest test_scraper.py -v
```

---

## 2. Approach, Assumptions, and Technical Details

### Investigation and Architecture
1. **Source Discovery**:
   - The official public portal `https://www.sijilat.bh` provides a public commercial search interface at `/public-search-cr/search-cr-2.aspx` and details viewer at `/public-search-cr/search-cr-3.aspx`.
   - Inspection of client scripts revealed that the portal is powered by a backend REST API at `https://api.sijilat.bh/api/`.
2. **Public Client Authentication**:
   - The frontend application authenticates requests by acquiring a short-lived JSON Web Token (JWT) from `https://api.sijilat.bh/token`.
   - Public client authentication uses client username `sijilat` and an HMAC-SHA256 encrypted password seed (`sijilat_test` signed with public client key `UHxNtYMRYwvfpO1dS5pWLKL0M2DgOj40EbN4SoBWgfc`).
   - The prototype replicates this authentication handshake purely in Python, allowing direct, reliable, and high-speed API communication without needing headless browsers (Selenium/Playwright) or fragile HTML DOM scraping.
3. **Data Retrieval Endpoints**:
   - `POST https://api.sijilat.bh/api/CRdetails/CompleteCRDetails` accepts `{ "cr_no": "<CR>", "branch_no": "<BRANCH>", "cult_lang": "EN" }`.
   - Returns complete company summary, branch catalog (`otherbranchlist`), commercial address (`commercialAddress`), and registered business activities (`businessActivities`).
4. **Assumptions**:
   - Public commercial registry access remains unauthenticated for basic company inquiries (no eKey or national ID required for public extract data).
   - Commercial registration numbers are numeric strings.
   - A business entity may have multiple branches; branch `1` is typically the head office/primary registration.
   - Sijilat API responses follow standard UTF-8 encoding supporting Arabic and English strings.

---

## 3. Provenance Classification: Distinguishing Absent vs. Unretrievable Data

To strictly separate **information that is absent from the source registry record** from **information that code could not extract or retrieve**, each data field is packaged with a provenance tag:

| Provenance Tag | Meaning | Example |
| :--- | :--- | :--- |
| `RETRIEVED` | The field was successfully retrieved and contained valid registry data. | Commercial Name: `"BAPCO REFINING B.S.C CLOSED"`, Town: `"AWALI"` |
| `ABSENT_FROM_SOURCE` | The field was queried, but the source returned `null`, empty string, whitespace, `N/A`, or `-`. | PO Box: `null`, Telephone: `null`, Website: `null` |
| `EXTRACTION_ERROR` | An upstream failure, network timeout, or parser mismatch prevented retrieval. | Simulated network failure, malformed branch payload |

### Multi-Branch Architecture
When an entity has multiple branches (as demonstrated by CR `48602` having 13 branches):
- Top-level `branch_catalog` maintains a full enumeration of all branches (identifiers 1 through 13), their individual names, statuses, and registration/expiry dates.
- Each branch in the `branches` array maintains its own distinct `branch_identifier`, status, activities, and commercial address.

---

## 4. Verification Results & Manual Comparison

A side-by-side manual verification was conducted between the live Sijilat web UI at:  
`https://www.sijilat.bh/public-search-cr/search-cr-3.aspx?cr_no=48602&branch_no=1`  
and the output generated in `output/cr_48602_run1.json`.

| Field | Live Source (Sijilat Web UI) | Prototype Output (`cr_48602_run1.json`) | Match? | Notes |
| :--- | :--- | :--- | :---: | :--- |
| **CR Number** | `48602` | `"48602"` | Exact | Correctly mapped |
| **Branch Identifier** | `1` | `"1"` | Exact | Primary branch identified |
| **Commercial Name (EN)** | `BAPCO REFINING B.S.C CLOSED` | `"BAPCO REFINING B.S.C CLOSED"` | Exact | Exact match |
| **Commercial Name (AR)** | `بابكو للتكرير ش.م.ب مقفلة` | `"بابكو للتكرير ش.م.ب مقفلة"` | Exact | Full Arabic text preserved |
| **Legal Form** | `Bahrain Shareholding Company (Closed)` | `"Bahrain Shareholding Company (Closed)"` | Exact | Code `10`, Nationality `BAHRAINI` |
| **Registration Status** | `UNDER MORTGAGE` (Black indicator) | `"UNDER MORTGAGE"`, Color `"Black"` | Exact | Accurately reflects legal restriction |
| **Registration Date** | `01/05/2002` | `"01/05/2002"` | Exact | Historical incorporation date |
| **Expiry Date** | `01/05/2027` | `"01/05/2027"` | Exact | Valid 5-year commercial license |
| **Building** | `245` | `"245"` | Exact | - |
| **Road** | `4511 (ROAD 2831)` | Road `"4511"`, Name `"ROAD 2831"` | Exact | Both code and road name captured |
| **Block** | `945` | `"945"` | Exact | - |
| **Town** | `AWALI` | `"AWALI"` | Exact | - |
| **Email** | `grouplitigation.hq@bapcoenergies.com` | `"grouplitigation.hq@bapcoenergies.com"` | Exact | - |
| **Mobile** | `( +973 ) 38121208` | `"( +973 ) 38121208"` | Exact | - |
| **PO Box** | Blank / Not displayed | `null` (`ABSENT_FROM_SOURCE`) | Exact | Correctly differentiated from error |
| **Website** | Blank / Not displayed | `null` (`ABSENT_FROM_SOURCE`) | Exact | Correctly differentiated from error |
| **Activities Count** | 3 Activities listed | 3 Activities extracted | Exact | ISIC `4661-5`, `701-1`, `4661-2` |

### Known Limitations
1. **Dynamic CAPTCHA / Rate-Limiting**: The public Sijilat API currently allows querying commercial registration details without an active CAPTCHA. If MOIC introduces Cloudflare Turnstile or reCAPTCHA v3 on the public endpoints, a headless browser session or CAPTCHA solving pipeline would be necessary.
2. **Authenticated Tier Data**: Certain sensitive corporate records (such as complete beneficial ownership shares, CPR national identification numbers of individual partners, or certified commercial registration extract PDFs) require an official Bahrain National eKey login and are intentionally not accessible via public lookup.
3. **Session Re-negotiation**: Public client JWTs expire after 3600 seconds. The client automatically refreshes tokens upon expiry, but long-lived parallel workers should manage tokens centrally.

---

## 5. Live vs. Local Testing Statement

- **Demonstrated on Live Source**:
  - Live token authentication (`https://api.sijilat.bh/token`).
  - Live search and multi-branch details extraction for CR `48602` (BAPCO REFINING B.S.C CLOSED, branches 1 to 13).
  - Repeat live execution verifying deterministic data consistency (`output/cr_48602_run1.json` vs `output/cr_48602_run2.json`).
  - Live negative test on non-existent CR `999999999` confirming `NOT_FOUND` response handling.
- **Tested Locally / Simulated**:
  - Simulated upstream network outage / connection timeout (`output/cr_48602_simulated_failure.json`), where `is_simulated: true` and `processing_outcome: "SIMULATED_FAILURE"` are explicitly recorded.
  - Automated unit test suite verifying mock edge cases and parser resilience (`test_scraper.py`).

---

## 6. Business Value & Research Task Replacement Analysis

### What Research Task This Replaces
- **Corporate Due Diligence & KYB Verification**: Eliminates manual navigation of the Bahrain Sijilat portal during client onboarding, supplier verification, and credit risk assessments.
- **Registry Compliance Auditing**: Replaces periodic manual checks of commercial registration status (e.g. checking whether a vendor's registration has lapsed, entered liquidation, or fallen under mortgage).
- **Activity Authorization Checks**: Automates verification that a counterparty is officially licensed to conduct the specific economic activities (ISIC codes) specified in commercial contracts.

### What Still Requires Human Review
- **Legal Impediment Nuance**: While the prototype captures statuses like `UNDER MORTGAGE`, `SUSPENDED`, or `DELETED WITH PAYMENT`, an experienced legal analyst must interpret the exact legal consequence of mortgages or ongoing restructuring.
- **Cross-Jurisdiction Ultimate Beneficial Ownership (UBO)**: Public registry data indicates legal partners or parent shareholdings, but tracing complex holding structures through Cayman, DIFC, or European parent entities requires forensic investigator synthesis.
- **Sanctions & Politically Exposed Persons (PEPs)**: Automated names must still be cross-referenced against global sanctions lists (OFAC, UN, EU) and local Bahrain gazettes.

### How to Measure Its Value
1. **Time Savings**: A trained compliance analyst spends ~6 to 10 minutes per commercial entity navigating Sijilat, resolving branches, translating Arabic descriptions, and transcribing details into internal databases. The prototype collects and normalizes the same record in **1.4 seconds** (>99% time reduction).
2. **Error Rate Reduction**: Direct API collection eliminates human transcription errors in registration dates, CR numbers, and ISIC activity codes.
3. **Cost per Inquiry**: Reduces marginal inquiry cost from ~$5–$10 in analyst labor to negligible computing overhead (<$0.001 per query).
4. **Throughput Scaling**: Allows an organization to audit a portfolio of 5,000 corporate counterparties in under an hour rather than taking months of manual review.

---

## 7. AI Assistance & Self-Verification Disclosure

- **AI Assistance Used**:
  - AI assisted in the rapid static analysis of minified JavaScript assets (`config.js`, `search-cr-script.js`, `search-cr-details.js`) from Sijilat's web frontend to decipher endpoint parameters and the HMAC-SHA256 client token generation algorithm.
  - AI assisted in structuring the modular Python script and writing comprehensive unit test scaffolds.
- **What Was Verified Personally**:
  - Live HTTP requests and status codes were inspected and executed directly against `api.sijilat.bh`.
  - The extracted JSON attributes (names, dates, address components, ISIC activities) were manually cross-referenced against the visual rendering on Sijilat's web interface.
  - Negative responses (`No Data Found`) and simulated fault states were verified for schema adherence.

---

## 8. Tool Selection Rationale & Role of AI

### Tool Selection
- **Python Standard Library (`urllib`, `hmac`, `hashlib`)**: Chosen over third-party frameworks (Selenium, Playwright, Scrapy) to guarantee zero setup friction, instant reproducibility on any evaluation machine, minimal resource usage, and immunity to browser driver version mismatches.
- **Direct API Protocol vs. DOM Scraping**: Sijilat renders data client-side via JavaScript. Targeting the underlying JSON endpoints provides far greater speed (1.4s vs 15s for headless Chromium), higher reliability against frontend HTML layout changes, and native structured data.

### Does AI Add Value to This Task?
**Yes, significantly**:
1. **Reverse-Engineering Acceleration**: Government registry portals frequently lack public API documentation. AI drastically reduces the time needed to deconstruct client-side auth logic, identify secret key seeds, and inspect request payload contracts from minutes of manual debugging to seconds.
2. **Schema & Provenance Modeling**: AI helps design clean, robust data schemas that anticipate real-world edge cases (such as the distinction between a field being absent in source records vs. failed extraction).
3. **Caveat**: AI alone cannot verify live registry stability or legal correctness—human-in-the-loop validation remains essential to confirm data integrity against official sources.
