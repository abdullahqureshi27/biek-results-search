# Project Progress & Research Notes

**Last updated: 2026-08-28**

This file is the single source of truth for where the project stands. Read this
first before working on the project — it records everything we researched so we
don't re-discover it.

> **Quick status:** All 3 Part II 2026 results are declared. PDFs are downloaded.
> The pksol web API is in a broken/transitional state — the BIEK mobile app works
> but the public API returns "No data found". We're waiting for PKSOL to update
> the web API. See Section 2 for details.

---

## 1. Current Status (BIEK Part II 2026)

| Group | Part II 2026 status | Gazetted on | Gazette PDF | Rolls extracted |
|---|---|---|---|---|
| Science Pre-Medical | **DECLARED** | 31-07-2026 | `pdfs/pm_part2.pdf` (180 pp) | `rollNumbers/pm_rolls.txt` — **14,207** (300006–390783) |
| Science Pre-Engineering | **DECLARED** | 17-08-2026 | `pdfs/se_part2.pdf` (154 pp) | `rollNumbers/se_rolls.txt` — **9,913** (800001–898101) |
| Science General | **DECLARED** | 27-08-2026 | `pdfs/sg_part2.pdf` (135 pp) | `rollNumbers/sg_rolls.txt` — **10,510** (600001–688451) |
| Humanities Regular/Private | DECLARED | 07/31-08-2026 | on board site | not downloaded |
| Economics / Special candidates | DECLARED | 31-07-2026 | on board site | not downloaded |
| Commerce | not announced | — | — | — |

Gazette URLs (official board site):
`https://www.biek.edu.pk/Result-2026/Annual/Part-II/<NAME>.pdf`
- PM: `SCIENCE%20PRE-MEDICAL.pdf`
- SE: `HSC%20PART-II-RESULT-GAZETTE-PRE-ENGINEERING-ANNUAL-2026-COMPLETE.pdf`
- SG: `HSC-RESULT-GAZETTE-SCIENCE%20GENERAL-PART-II-ANNUAL-2026-COMPLETE.pdf`

**Roll number patterns — IMPORTANT (they differ from Part I):**
- Part II 2026: PM = `3xxxxx`, SE = `8xxxxx`, SG = `6xxxxx`
- Part I 2025 (archived): PM = `4xxxxx`, SG = `7xxxxx`

---

## 2. The Results API (how full details are fetched)

- **Endpoint:** `POST https://api.pksol.com/search` — same API the Part I project used.
- **Official portal that uses it:** `https://biekresult.pksol.com/` (confirmed by reading its JS).
- **Payload:**
  ```json
  {"faculty": "sm", "value": "reg-p2-a-2026", "roll_no": "312204", "matric_roll_no": "312204"}
  ```
  - `faculty`: sm | se | sg | hmt | com
  - `value` = exam code, format `reg-{p1|p2}-{a|s}-{year}` (`a` = annual, `s` = supply)
  - `matric_roll_no` is optional (portal only sends it if filled)
- **Response:** `detail: {roll_no, applicant_name, father_name, secured_total, grade}` + `result: {theory[], practical[]}`
- **Live list of valid exam codes:** `GET https://api.pksol.com/parameters`

### ⚠️ CRITICAL: the API is in a BROKEN / TRANSITIONAL state

**What happened (August 2026):**
PKSOL changed the API field format but hasn't fully deployed it:

| Aspect | Old format | New format |
|---|---|---|
| Exam code field | `exam_code` | `value` |
| Faculty field | *(not required)* | `faculty` (required) |
| Old format result | 500 error (missing `faculty`) | — |
| New format result | — | `No data found` (even for 2025 rolls) |

**Current API state (2026-08-28):**
- `/parameters` lists only 3 old 2025 exam codes
- Website dropdown (`biekresult.pksol.com`) only shows 2025 Supply options
- New format (`value`+`faculty`) accepts requests but returns `No data found` for everything
- Old format (`exam_code`) throws 500 error
- **The BIEK mobile app (`com.biek.edu.app`) WORKS** — it uses the same `value`+`faculty` format and has 2026 data
- The app likely uses a different API URL or requires authentication that isn't publicly documented

**Verified working example (from app screenshots):**
```json
POST https://api.pksol.com/search
{"faculty":"sg","value":"reg-p2-a-2026","roll_no":"607192"}
→ Name: MUHAMMAD ABDULLAH, Father: MUHAMMAD MOBIN QURESHI, Marks: 582, Grade: C, PASS
```

**Conclusion:** The scripts are ready for the new format. Once PKSOL loads 2026 data into the web API, bulk search will work immediately.

**Exam codes tested and rejected:** `reg-p2-2026`, `reg-p2-annual-2026`, `p2-a-2026`, `reg-part2-2026`, `reg-sg-p2-a-2026`, plus int/GET/cookie+CSRF variants.

**How to find the app's real API (if needed):**
Use mitmproxy to intercept the app's network traffic:
```bash
pip install mitmproxy
mitmproxy --listen-port 8080
# Set phone proxy to YOUR_PC_IP:8080, install CA cert from mitm.it
# Open BIEK app → search → watch mitmproxy for the real API URL/headers
```

---

## 3. Gazette format (how rolls/marks are extracted)

- Data pages list students as `ROLL(MARKS)`, e.g. `312204(798)`, marks may have grace like `767+ 3` or `559^ 2`.
- Absent candidates appear as `***********` (no roll extractable).
- **Part I gazettes:** students listed in roll order within each college section; sections grouped by paper count (`1Paper`, `2 Papers` … `6 Papers`).
- **Part II gazettes:** students grouped by **grade** (Grade A-1 → A → B → C → D → E); within each grade the rolls are ascending.
- **No names** in the data pages of either gazette (names only on the merit/position pages, top ~10 only).
- Extraction regex (in `scripts/extract_rolls_from_pdf.py`): `(?<!\d)(\d{6})\(` — negative lookbehind (not `\b`) is required so rolls glued to a grade header (e.g. `Grade : A320407(998)`) are still matched. The `\b` version silently lost ~1,000 rolls.
- Per-college stats tables exist in Part II gazette (Registered/Absent/Appeared/Passed by grade) — used to cross-check extraction.
- `pdfplumber` (installed in `.venv` only, not in pyproject) is needed for layout-accurate extraction (column/reading order) — PyPDF2 text is column-jumbled.

---

## 4. Part I → Part II roll mapping (RESEARCHED — no public solution)

**Question:** can we get a student's Part II roll from their Part I roll?
**Answer: No reliable public method exists.** Everything below was tested:

- ❌ **No numeric relationship:** Part I PM 4xxxxx → Part II PM 3xxxxx has NO digit pattern (only ~13.5% share last-5 digits = random chance).
- ❌ **Gazettes have no cross-reference:** no "previous roll" columns anywhere; no names to match on.
- ❌ **Board portals:** `portal.biek.edu.pk` (enrolment tracking, needs per-student CNIC/application), `admitcard.biek.edu.pk/ACPartII` (search by Challan No / Matric Roll No, govt colleges only, not released yet), no public roll-search path (probed 10+ URLs, all 404).
- ❌ **Historical:** a 2020-era feature let students search Part II roll by "Admission Form No or Part I roll" — not available on current portals.
- ⚠️ **Positional estimate (weak):** both gazettes list students per college in the same order, so a Part I roll's position in its college section can be mapped to a candidate Part II roll — but Part II is grade-grouped and ~57% of PM students failed (not listed), so it's an approximation only.

**Only reliable sources for a Part II roll:** the student's college (roll slip/admit card), or — once the API has data — try passing the Part I roll to the search (untested, some portals accept previous-year rolls).

**Worked example (roll 439626, Part I 2025 PM):**
- College: **Riaz Govt. Girls College Liaquatabad No. 10** (confirmed via column-layout analysis + stats cross-check: Part I section 439581–439891 = 296 rolls vs Part II stats 294 registered)
- Part I: marks 364, position #23 in the college section
- Part II candidate window (if passed): 317380–317413; exact positional match 317391 — **unverified**
- Riaz's full Part II passed block (123 rolls): grades A-1 (4): 317450,317481,317503,317539 · A (8): 317448,317484,317504,317518,317554,317585,317634,317645 · B (42): 317391–317651 · C (59): 317396–317648,360616 · D (10): 317393,317475,317521,317547,317548,317575,317640,360605,360613,360615

---

## 5. Decisions already made (don't re-litigate)

- ❌ **SMS method** (BIEK roll → 8583) — user rejected.
- ❌ **Third-party aggregators** (hamariweb = Cloudflare-blocked, ilmkidunya = backend not exposed, fragile/ToS risk) — not the "same way as Part 1".
- ❌ **KPK board scripts** — moved to `archive/kpk/` (endpoints were placeholders).
- ✅ **Part I 2025 data** — moved to `archive/part1/` (PDFs, rolls, results, `check_duplicates.py`, `find_missing.py`).
- ✅ **Scripts are configured for Part II 2026** (`reg-p2-a-2026` default in `biek_scraper.py` + `bulk_search_all.py`).

---

## 6. Open items / next steps

1. **🔴 Watch the API** — poll `https://api.pksol.com/parameters`; the moment 2026 codes appear with `value`+`faculty` format, bulk search works as-is. Quick check: `curl https://api.pksol.com/parameters`.
2. **✅ Extract SG rolls** — DONE. 10,510 rolls (600001–688451) saved to `rollNumbers/sg_rolls.txt`.
3. **🟡 Trace the app's API** — use mitmproxy to capture the BIEK app's network traffic. The app works but the web API doesn't — finding the app's endpoint could unlock 2026 data immediately.
4. **When data loads:** test whether the Part I roll works in the search (`roll_no=<part1 roll>`, `value=reg-p2-a-2026`) — one request per roll, cheap to try.
5. **Optional:** gazette parser to build results CSV directly from PDFs (roll + marks + grade only — **no names**, so it's a partial fallback while the API is empty).
6. **Optional:** college-wise positional mapping tool (Part I roll → candidate Part II roll) — approximation only, needs manual verification.
7. **Cleanup:** `pdfplumber` is installed in `.venv` but not declared in `pyproject.toml` — decide whether to keep (used for layout extraction) or remove.

---

## 7. Key commands

```bash
# Extract rolls from a Part II gazette
python scripts/extract_rolls_from_pdf.py --pdf pdfs/pm_part2.pdf --output rollNumbers/pm_rolls.txt
python scripts/extract_rolls_from_pdf.py --pdf pdfs/sg_part2.pdf --output rollNumbers/sg_rolls.txt

# Sequential search (Part II 2026 default)
python scripts/biek_scraper.py --file rollNumbers/pm_rolls.txt --faculty sm --output results/pm_results.csv

# Fast parallel bulk search
python scripts/bulk_search_all.py --file rollNumbers/pm_rolls.txt --faculty sm --output results/pm_results.csv --workers 20

# Check API exam codes
curl https://api.pksol.com/parameters

# Test one roll against the API (new format: value + faculty)
curl -s -X POST https://api.pksol.com/search -H "Content-Type: application/json" \
  -d '{"faculty":"sg","value":"reg-p2-a-2026","roll_no":"607192"}'

# Trace the BIEK app's real API (requires phone proxy setup)
pip install mitmproxy && mitmproxy --listen-port 8080
```
