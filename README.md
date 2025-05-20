# Async Web Scraper

This project is a compact, fully-asynchronous Python scraper that walks the
*List of programming languages* page on Wikipedia, opens every linked language
article, and harvests the language name together with its creator (when that
information exists).  
The whole job is under 100 lines of code yet demonstrates practical use of
`asyncio`, `aiohttp`, and `BeautifulSoup` for high-throughput data gathering. :contentReference[oaicite:0]{index=0}:contentReference[oaicite:1]{index=1}

---

## Table of contents
1. [Features](#features)  
2. [Requirements](#requirements)  
3. [Installation](#installation)  
4. [Quick start](#quick-start)  
5. [Project walkthrough](#project-walkthrough)  
6. [Saving to CSV / other outputs](#saving-the-results)  
7. [Extending the scraper](#extending-the-scraper)  
8. [Troubleshooting](#troubleshooting)  
9. [License](#license)

---

## Features<a id="features"></a>

* **Asynchronous networking** — pages are fetched concurrently with
  `aiohttp`, giving a significant speed boost compared to sequential
  requests. :contentReference[oaicite:2]{index=2}:contentReference[oaicite:3]{index=3}  
* **Automatic link discovery** — the script first scrapes
  `https://en.wikipedia.org/wiki/List_of_programming_languages`,
  collects every language link inside the `<div class="div-col">` list, and
  queues them for processing. :contentReference[oaicite:4]{index=4}:contentReference[oaicite:5]{index=5}  
* **HTML parsing with BeautifulSoup** — pulls the language name from the
  page’s infobox caption and attempts to grab the creator / designer from the
  corresponding table rows. :contentReference[oaicite:6]{index=6}:contentReference[oaicite:7]{index=7}  
* **Pretty-print output** — results are currently printed as a Python list
  so you can inspect them quickly in the console. :contentReference[oaicite:8]{index=8}:contentReference[oaicite:9]{index=9}  
* Zero external framework overhead — everything is plain Python,
  making the script easy to read, hack, and repurpose.

---

## Requirements<a id="requirements"></a>

| Package          | Minimum version |
| ---------------- | --------------: |
| Python           | 3.8 recommended |
| aiohttp          | 3.9            |
| BeautifulSoup4   | 4.12           |
| (optional) pandas † | 2.2           |

† Only needed if you want to analyse data or write a CSV directly from a
Jupyter notebook.

---

## Installation<a id="installation"></a>

```bash
# 1 – clone / download the repo
git clone https://github.com/your-user/async-wikipedia-scraper.git
cd async-wikipedia-scraper

# 2 – (recommended) create & activate a virtual environment
python -m venv .venv
source .venv/bin/activate           # Windows: .venv\Scripts\activate

# 3 – install dependencies
pip install aiohttp beautifulsoup4
```

## Quick start<a id="quick-start"></a>
Run the scraper from the command line:

```bash
python scraper.py
```
You’ll see a pretty-printed Python list where each inner list is
[language_name, creator]. Expect the first few rows to look like:
['ABC', 'CWI, Guido van Rossum']
['ActionScript', 'Gary Grossman']
['Ada', 'Jean Ichbiah']
...
Total run-time on a modern laptop is ~10-15 seconds thanks to asynchronous
fetching.

## Project walkthrough<a id="project-walkthrough"></a>
Section in scraper.py	What it does
BASE_URL & crawl()	Fetches the master list page and extracts every <a> in the multi-column div. 

fetch(url)	Re-usable coroutine that opens a URL with aiohttp and returns raw HTML. 

scrape(link)	Parses one language article, picking out the name (infobox caption) and the row containing “Developer” / “Designed by”. 

main()	Orchestrates crawling + scraping via asyncio.gather, then pretty-prints the full list. 


Feel free to open the file while reading the table above for line-by-line
context.

## Saving the results<a id="saving-the-results"></a>
Right now the script prints to stdout.
To save a CSV, replace the last three lines of main() with:

```python
import csv
with open("languages.csv", "w", newline="", encoding="utf-8") as fh:
    writer = csv.writer(fh)
    writer.writerow(["Language", "Creator"])
    writer.writerows(authors)
print("Saved -> languages.csv")
```
Or, inside a Jupyter notebook:

```python
import pandas as pd
df = pd.DataFrame(authors, columns=["Language", "Creator"])
df.to_csv("languages.csv", index=False)
```

## Extending the scraper<a id="extending-the-scraper"></a>
- Different Wikipedia list — change BASE_URL and the path fed to crawl(), then tweak the CSS selector that gathers links.
- Richer infobox fields — inspect the target page with DevTools, update the select_one() calls in scrape() to pull extra columns (e.g. first appeared, file extension).
- Other sites — swap the crawl() logic for any list or sitemap, keep the rest of the code unchanged.
- Concurrency limit — for fragile hosts add a semaphore or simply wrap aiohttp.ClientSession() in a global semaphore to reduce parallelism.

## Troubleshooting<a id="troubleshooting"></a>
Symptom	Fix
ImportError: aiohttp not found	Run pip install aiohttp inside your activated venv.
Endless redirects / 403 errors	Wikipedia occasionally rate-limits; wait a minute or lower concurrency.
RuntimeError: Event loop is closed (Windows + Python < 3.11)	Replace asyncio.run(main()) with a custom event-loop policy or upgrade Python.

## License<a id="license"></a>
Released under the MIT License — see LICENSE for details.

### Happy scraping 🕸️
