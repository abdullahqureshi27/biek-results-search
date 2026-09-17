# Project Progress & Research Notes

**Last updated: 2026-09-18**

This file is the single source of truth for where the project stands. Read this
first before working on the project — it records everything we researched so we
don't re-discover it.

> **Quick status:** 🎉 **BREAKTHROUGH: The API endpoint mystery is SOLVED!**
> Analysis of the official BIEK Android app (`com.biek.edu.app`, Flutter binary)
> revealed that while the broken web portal uses `api.pksol.com`, the mobile app uses
> **`http://api.biekedu.com/search`**.
> Part II 2026 data is fully live and populated on this endpoint. All scripts
> (`biek_scraper.py`, `bulk_search_all.py`) have been updated and verified with live lookups!

---

## 1. Current Status (BIEK Part II 2026)

| Group | Part II 2026 status | Gazetted on | Gazette PDF | Rolls extracted | API Status |
|---|---|---|---|---|---|
| Science Pre-Medical | **DECLARED** | 31-07-2026 | `pdfs/pm_part2.pdf` (180 pp) | `rollNumbers/pm_rolls.txt` — **14,207** (300006–390783) | **VERIFIED WORKING** |
| Science Pre-Engineering | **DECLARED** | 17-08-2026 | `pdfs/se_part2.pdf` (154 pp) | `rollNumbers/se_rolls.txt` — **9,913** (800001–898101) | **VERIFIED WORKING** |
| Science General | **DECLARED** | 27-08-2026 | `pdfs/sg_part2.pdf` (135 pp) | `rollNumbers/sg_rolls.txt` — **10,510** (600001–688451) | **VERIFIED WORKING** |
| Humanities Regular/Private | DECLARED | 07/31-08-2026 | on board site | not downloaded | supported (`hmt`) |
| Commerce | not announced | — | — | — | supported (`com`) |

Gazette URLs (official board site):
`https://www.biek.edu.pk/Result-2026/Annual/Part-II/<NAME>.pdf`
- PM: `SCIENCE%20PRE-MEDICAL.pdf`
- SE: `HSC%20PART-II-RESULT-GAZETTE-PRE-ENGINEERING-ANNUAL-2026-COMPLETE.pdf`
- SG: `HSC-RESULT-GAZETTE-SCIENCE%20GENERAL-PART-II-ANNUAL-2026-COMPLETE.pdf`

**Roll number patterns — IMPORTANT (they differ from Part I):**
- Part II 2026: PM = `3xxxxx`, SE = `8xxxxx`, SG = `6xxxxx`
- Part I 2025 (archived): PM = `4xxxxx`, SG = `7xxxxx`

---

## 2. The Results API (Mobile App Production Endpoint)

- **Production Endpoint:** `POST http://api.biekedu.com/search`
- **Parameters Endpoint:** `GET http://api.biekedu.com/parameters`
  - Returns live 2026 exam codes: `reg-p2-a-2026` (Regular) and `pvt-p2-a-2026` (Private)
- **Headers:**
  ```http
  User-Agent: Dart/3.4 (dart:io)
  Content-Type: application/json; charset=utf-8
  ```
- **Payload:**
  ```json
  {"faculty": "sg", "value": "reg-p2-a-2026", "roll_no": "607192"}
  ```
  - `faculty`: sm | se | sg | hmt | com
  - `value`: `reg-p2-a-2026` or `pvt-p2-a-2026`
  - `matric_roll_no`: optional
- **Response Format:**
  ```json
  {
    "detail": {
      "roll_no": 607192,
      "applicant_name": "MUHAMMAD ABDULLAH",
      "father_name": "MUHAMMAD MOBIN QURESHI",
      "secured_total": 582,
      "grade": "C"
    },
    "result": { "theory": [], "practical": [] }
  }
  ```
- **When Roll Is Not Found:**
  ```json
  {"detail":{"roll_no":null,"applicant_name":null,"father_name":null,"secured_total":null,"grade":null},"result":{"theory":[],"practical":[]}}
  ```

### 💡 Root Cause of Past Confusion (`api.pksol.com` vs `api.biekedu.com`):
PKSOL maintains two domains:
1. `api.pksol.com`: The legacy web API used by `biekresult.pksol.com`, which remains unpopulated for 2026 (returns `No data found`).
2. `api.biekedu.com`: The dedicated backend used by the official Flutter mobile app (`com.biek.edu.app`), which has all 2026 data live. Note: use HTTP (`http://`), as HTTPS handshake on this host can reset under certain TLS configurations.
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

1. **✅ Discover & verify Mobile App API** — DONE! Found `http://api.biekedu.com/search`, fully working for Part II 2026 data.
2. **✅ Extract all Part II rolls** — DONE (PM: 14,207, SE: 9,913, SG: 10,510).
3. **✅ Update scripts** — DONE (`biek_scraper.py` and `bulk_search_all.py` configured with `http://api.biekedu.com/search`).
4. **Ready for bulk execution:** Run `bulk_search_all.py` to produce full CSV results for each faculty group.
5. **Optional:** test whether Part I roll numbers match in the search endpoint.
6. **Cleanup:** `pdfplumber` is installed in `.venv` — declare in `pyproject.toml` or keep as optional tool.

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
python scripts/bulk_search_all.py --file rollNumbers/sg_rolls.txt --faculty sg --output results/sg_results.csv --workers 20
python scripts/bulk_search_all.py --file rollNumbers/se_rolls.txt --faculty se --output results/se_results.csv --workers 20

# Check API exam codes
curl http://api.biekedu.com/parameters

# Test one roll against the API
python -c "import requests; print(requests.post('http://api.biekedu.com/search', json={'faculty':'sg','value':'reg-p2-a-2026','roll_no':'607192'}, headers={'User-Agent':'Dart/3.4 (dart:io)'}).text)"
```
