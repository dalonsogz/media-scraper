# AGENTS.md

## Project Overview
Personal media scraper: downloads game data pages from TheGamesDB (https://thegamesdb.net/game.php?id=<id>),
parses them with BeautifulSoup and stores structured items in MongoDB.

## Tech Stack
- Python 3.10 (project venv in ./venv, base interpreter E:\python310)
- requests, beautifulsoup4, pyyaml, pymongo
- MongoDB at localhost:27017 (db: thegamesdb, collection: items)

## Setup / Run
- pip install -r requirements.txt
- Start local MongoDB
- Run: web_scraper.cmd  OR  .\venv\Scripts\python.exe web_scraper.py
- Logs: config.yml; per-run file web_scraping_<baseName>.log (logger name: web_scraper, DEBUG)

## Architecture
- web_scraper.py: main orchestration (download -> save -> mark processed -> parse -> store)
- itemTheGamesdb.py: per-site abstraction (TheGamesDBConfig, TheGamesDBItem, TheGamesDBMethods, TheGamesDBMongo)
- renew_proxies.py: standalone proxy renewal script (sources + health check + merge)
- remove_duplicates.py: standalone script automating the historical DELETE DUPLICATED ITEMS procedure (Mongo aggregation -> duplicated.txt -> duplicated_ids.txt -> delete by _id)

## Main Flow
- main() sets processFrom/processTo in web_scraper.py -> dowloadAndParseItems()
- downloadItems(): ThreadPoolExecutor(max_workers=maxConcurrentRequests=2) submits _downloadItem tasks from notProcessedItems; save raw HTML; mark processed; sleep
- _downloadItem(): per-item task (request -> renew/retry on total proxy failure -> process -> save -> sleep)
- common_requests(): direct or proxies from proxies.txt; min content size check; maxProxyFails handling; 429/503 tolerance (skip to next proxy, do not mark failed); mark_failed_proxies wrapped in proxy_lock
- renewProxies(): hybrid renewal (proactive if list empty at start, reactive on total failure -> renew -> retry once); sources; health check; merges existing + new; keeps only healthy proxies
- parseItemFilesAndAddToDabase(): checks Mongo by id before parsing; inserts via toJson; collects fails

## Key Flags (web_scraper.py)
- addToDatabase, downloadIfExists, addIfExists
- maxConcurrentRequests = 2 (ThreadPoolExecutor for downloads)
- minTimeBtwRequest = 1, maxTimeBtwRequest = 3 (random sleep between requests)
- maxProxyFails = 2, minValidContenSizeBytes = 3000

## Proxy Renewal (renew_proxies.py)
- Strategy: hybrid (proactive + reactive). Merge existing + new; health check all candidates; write only healthy.
- Sources (all tried, proxies collected from each successful source): clarketm raw (https://raw.githubusercontent.com/clarketm/proxy-list/master/proxy-list-raw.txt, primary), monosans (https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/http.txt, fallback). FreeProxyList (tonysss) removed: DNS fails from this env. clarketm branch must be master; monosans returned ~45% alive in sample.
- Health check: GET https://thegamesdb.net/ via proxy, status 200 -> healthy (concurrent, 10 workers, timeout 5s).
- IMPORTANT: renewProxies must health check ALL merged proxies (existing + new) before writing; previously existing proxies were kept unconditionally without check, which let dead proxies persist in proxies.txt.
- proxies.txt: lines starting with # disabled; schemes http/https/socks4/socks5; bare host assumed http; renewed entries normalized bare->http://.

## Performance
- Phase 1 done: requests session keep-alive per thread (get_session/threading.local); requests via self.get_session()
- Phase 2 done: ThreadPoolExecutor(max_workers=maxConcurrentRequests=2) in downloadItems; per-item task in _downloadItem
- Phase 2 done: tolerance 429/503 in common_requests (try next proxy, do not mark failed)

## Gotchas
- processedItems_thegamesdb.txt: one int per line, CRLF endings
- maxProxyFails = 2 (docstring of mark_failed_proxies mentions 5 - outdated)
- Fail handling: RuntimeError from all proxies -> renew -> retry -> if fails again SystemExit(1)
- Log files written by PowerShell redirection may come out UTF-16 (BOM) - use appropriate readers

## WIP / Known Issues
- TheGamesDBMongo.findTitleSimilar ($text) not integrated
- Web research tools (websearch/webfetch) were failing during this session (HTTP 402 / transport error) - proxy sources couldn't be fully validated live
- Proxy source availability varies (tonysss DNS fails from this env; clarketm branch master required; monosans partial health)
- Phase 3 pending: advanced proxy quality/health-check (latency, protocol filtering)
- proxies.txt currently holds 105 healthy proxies after renewal fixes
