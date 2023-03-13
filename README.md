# media-scraper

Web scrapping scripts testing capabilities with Python [BeautifulSoup](https://www.crummy.com/software/BeautifulSoup/) library.

Main script, web_scraper.py, fetch and update data from the site 'thegamesdb' site.

Script itemTheGames.DB.py, could be the template to achieve web scraping of other sites. 

OOP is used as a POC (Java interfaces pattern) to achieve the decoupling between the main script and the target site (WIP).

Results are stored in a mongodb database.

## DELETE DUPLICATED ITEMS

Delete (one) duplicated records searching by a field.
- launch the query to find duplicates by the field 'id':
~~~
DBQuery.shellBatchSize = 5000;
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

## Other scripts included

- mongoTest.py.  
Testing mongo search capabilities.
 
- requestTest.py.  
Testing different REST methods endpoints requests.

- requestFiles.py
Testing web batch fetching similar named resources.

- nes_midi_scraper.py.  
Code from [Twilio Blog article]() showing how to perform simple web scrapping using BeautifulSoup.
