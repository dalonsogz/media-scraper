# AGENTS.md

## Project Overview
Personal media scraper: downloads game data pages from TheGamesDB (https://thegamesdb.net/game.php?id=),
parses them with BeautifulSoup and stores structured items in MongoDB.

## Tech Stack
- Python 3.10 (project venv in ./venv, base interpreter E:\python310)
- requests, beautifulsoup4, pyyaml, pymongo
- MongoDB at localhost:27017 (db: thegamesdb, collection: items)

## Setup / Run
- pip install -r requirements.txt
- Start local MongoDB
- Run: web_scraper.cmd  OR  .\venv\Scripts\python.exe web_scraper.py
  - Logs: config.yml; per-run file web_scraping_.log (logger name: web_scraper, DEBUG)

## Architecture
- web_scraper.py: main orchestration (download -> save -> mark processed -> parse -> store)
- itemTheGamesdb.py: per-site abstraction (TheGamesDBConfig, TheGamesDBItem, TheGamesDBMethods, TheGamesDBMongo)

## Main Flow
- main() sets processFrom/processTo in web_scraper.py -> dowloadAndParseItems()
- downloadItems(): random pick from unprocessed ids in range; save raw HTML; mark processed; sleep random(min,max)
- common_requests(): direct or proxies from proxies.txt; min content size check; maxProxyFails handling
- parseItemFilesAndAddToDabase(): checks Mongo by id before parsing; inserts via toJson; collects fails

## Key Flags (web_scraper.py)
- addToDatabase: whether to insert into DB
- downloadIfExists / addIfExists: skip download / skip add if already present

## Gotchas
- processedItems_thegamesdb.txt: one int per line, CRLF endings
- proxies.txt: lines starting with # are comments; schemes http/https/socks4/socks5; bare host assumed http
- maxProxyFails = 2 (docstring of mark_failed_proxies mentions 5 - outdated)
- Sleep between requests: random.randint(minTimeBtwRequest, maxTimeBtwRequest) = 3..7

## WIP / Known Issues
- TheGamesDBMongo.findTitleSimilar (MongoDB $text search) not yet integrated
- Fail handling: RuntimeError from all proxies -> SystemExit(1)
