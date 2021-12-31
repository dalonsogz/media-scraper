from pymongo import MongoClient
from itemTheGamesDB import TheGamesDBItem
from bson import SON as bson

mongoClient = MongoClient(host="localhost", port=27017)
mongoDb = mongoClient.thegamesdb
mongoCol = mongoDb.items

# db.getCollection('items').createIndex({title: 'text'})
# db.getCollection('items').find({$text: {$search: 'Halo 3'}}, {score: {$meta: 'textScore'}}).sort({score: {$meta: 'textScore'}})


class RequestMongo:
    def common_request(self, title, maxResults):
        metaTextScore = bson({'$meta': 'textScore'})
        filter = bson({'$text': {'$search': title}})
        fields = bson({'_id': 0, 'id': 1, 'title': 1, 'platform': 1, 'score': metaTextScore})
        # query: {"$text": {"$search": title}},{'_id':0,'id':1,'title':1,'score':{'$meta':'textScore'}}).limit(15)
        cursor = mongoCol.find(filter, fields).limit(maxResults)
        cursor.sort([('score', metaTextScore)])
        return cursor

    def main(self):
#        query = "{$text: {$search: title}}, {score: {$meta: 'textScore'}}).sort({score: {$meta: 'textScore'}}"
        items = self.common_request('Nier Automata',10)
        for item in items:
            print(item)


def main():
    RequestMongo().main()


if __name__ == "__main__":
    main()
