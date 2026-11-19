# media-scraper

Web scrapping scripts testing capabilities with Python [BeautifulSoup](https://www.crummy.com/software/BeautifulSoup/) library.

Main script, web_scraper.py, fetch and update data from the site 'thegamesdb' site.

Script itemTheGames.DB.py, could be the template to achieve web scraping of other sites. 

OOP is used as a POC (Java interfaces pattern) to achieve the decoupling between the main script and the target site (WIP).

Results are stored in a mongodb database.

## How it works

Main script, web_scraper.py, orchestrates the full cycle for a given item range:

1. **Download**: `downloadItems()` fetches the game pages from TheGamesDB through `common_requests()` (direct connection or proxies), saves the raw HTML per item and marks it as processed in `processedItems_thegamesdb.txt`.
2. **Parse**: `parseHtml()` parses the saved HTML with BeautifulSoup and builds the structured item.
3. **Store**: `parseItemFilesAndAddToDabase()` stores the parsed item in MongoDB, only inserting it when the `id` is not already present (controlled by the `addIfExists` flag).

Main flags in `web_scraper.py`: `addToDatabase`, `downloadIfExists`, `addIfExists`, `maxConcurrentRequests`, `minTimeBtwRequest`, `maxTimeBtwRequest`, `maxProxyFails`, `minValidContenSizeBytes`.

## Proxy renewal

`renew_proxies.py` implements the hybrid proxy renewal workflow used by `web_scraper.py`:

- **Proactive**: if the proxy list is empty at startup, it renews it.
- **Reactive**: if all proxies fail during a download, it renews, reloads and retries once; if it fails again, the scraper exits.

Renewal gathers proxies from multiple sources (FreeProxyList, clarketm, monosans), merges them with the existing ones and health checks all candidates (concurrent requests to https://thegamesdb.net/, 10 workers, 5s timeout). Only healthy proxies are written to `proxies.txt`.

## DELETE DUPLICATED ITEMS

> **Historical**: this manual procedure is superseded by [`remove_duplicates.py`](remove_duplicates.py), which automates the same steps. It is kept in this document for reference only.

Delete (one) duplicated records searching by a field.
- launch the query to find duplicates by the field 'id':
~~~
DBQuery.shellBatchSize = 500000;
db.getCollection('items').aggregate(
    [
    { $match: { "id":{$gt:1}}}
    ,{ $group: { 
        _id: { id: "$id" },
        count: { $sum: 1 },
        docs: { $push: "$_id" }
    }}
    ,{ $match: { count:{$gt:1} }}
    ,{ $sort: { "_id.id":1} }
    ]
)
~~~
- copy results to `duplicated.txt`.

- copy the cleaned results to `duplicated_ids.txt`:
~~~
grep -Eo 'ObjectId\(\".*\"\),' duplicated.txt > duplicated_ids.txt
~~~
- edit `duplicated_ids.txt` to write the query to delete the `ObjectIds`, enclosing then in this way:
~~~
print(
db.getCollection('items').remove({
    "_id": {
        $in: [
            ObjectId("0930292929292929292929"),
            ....
            ObjectId("0920292929292929292929")
        ]
     }
})
) 
~~~
- launch the query with mongo shell:
~~~
mongo thegamesdb duplicated_ids.txt
~~~

## Remove duplicated items

`remove_duplicates.py` implements the automated version of the historical procedure above:

- Runs the MongoDB aggregation to find duplicated items by `id`.
- Writes the raw results to `duplicated.txt`.
- Extracts the duplicated `ObjectId`s and writes them to `duplicated_ids.txt`.
- Deletes the documents by `_id` using `$in`.

Run it with:
~~~
python remove_duplicates.py
~~~

## Get sorted/limited lists in mongoDB:

Get last 10 records:
~~~
db.getCollection('items').find().skip(db.getCollection('items').count()-10)
~~~
Get last 10 records (reverse order):
~~~
db.getCollection('items').find().sort({$natural:-1}).limit(10)
~~~
Get a record by th 'id':
~~~
db.getCollection('items').find({"id":104370}).sort({"id":1})
~~~
