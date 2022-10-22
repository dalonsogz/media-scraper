# media-scraper

## --

### DELETE DUPLICATED ITEMS

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
