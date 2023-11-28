import logging
import re
import json
from pymongo import MongoClient
from bson import SON as bson

class SteamStoreConfig:
    totalNumItems = 1174180

    urlBase = "https://store.steampowered.com/app/"
    itemDataFilePattern = "steampowered_{}.html"
    destFilePath = "steampowered"

    mongoClient = MongoClient(host="localhost", port=27017)
    mongoDb = mongoClient.steamstore
    mongoCol = mongoDb.items

    def config(self):
        return self.totalNumItems, self.urlBase, self.itemDataFilePattern, self.destFilePath, self.mongoCol

class SteamStoreItem:
    id = 0
    title = ""
    description = ""
    review_type_all = 0
    review_type_positive = 0
    review_type_negative = 0
    purchase_type_all = 0
    purchase_type_steam = 0
    purchase_type_non_steam = 0


    reviews_dict = {
        "review_type_all": "review_type_all",
        "review_type_positive": "review_type_positive",
        "review_type_negative": "review_type_negative",
        "purchase_type_all": "purchase_type_all",
        "purchase_type_steam": "purchase_type_steam",
        "purchase_type_non_steam": "purchase_type_non_steam",
    }

class SteamStoreMethods:

    def uncapitalize(s):
        return s[:1].lower() + s[1:]

    def toString(item):
        return "id:{}\ntitle:{}\ndescription:{}".format(
            item.id, item.title, item.description)

    def toJson(item):
        logging.debug("\n---------------------------------------------------------------------------------------------------------------------------------------\n")
        strJson = json.dumps(item, default=lambda o: o.__dict__, indent=4)
        jsonResult = json.loads(strJson)
        logging.debug("\n---------\n" + json.dumps(jsonResult, sort_keys=True, indent=4) + "\n---------\n")
        logging.debug("\n---------------------------------------------------------------------------------------------------------------------------------------\n")
        return jsonResult

    def findItemTitle(soup):
        tag = soup.find("span", itemprop="name")
        if tag:
            return tag.text.strip()

    def findItemDescription(soup):
        tag = soup.find("p", class_="game-overview")
        if tag:
            return tag.text.strip()

    def convertUserReviewsCount (tag):
        return int(''.join(re.findall(r'\d+', str(tag.string))))

    def setUserReviews(soup,item):
        tagsSpanReviewsCount = soup.find_all("span", class_="user_reviews_count")
        if tagsSpanReviewsCount:
            for tag in tagsSpanReviewsCount:
                tagParentFor = SteamStoreItem.reviews_dict.get(tag.parent["for"])
                if tagParentFor:
                    setattr(item, tagParentFor, SteamStoreMethods.convertUserReviewsCount(tag))

    def parseHtml(index, soup):
        item = SteamStoreItem()
        config = SteamStoreConfig()
        item.id = index
        item.title = SteamStoreMethods.findItemTitle(soup)
        item.description = SteamStoreMethods.findItemDescription(soup)
        SteamStoreMethods.setUserReviews(soup,item)
        return item

class SteamStoreMongo:

    @classmethod
    def findTitleSimilar(self,title,maxResults):
        metaTextScore = bson({'$meta': 'textScore'})
        filter = bson({'$text': {'$search': title}}) #, 'platform': 'PC' })
        fields = bson({'_id': 0, 'id': 1, 'title': 1, 'platform': 1, 'score': metaTextScore})
        # query: {"$text": {"$search": title}},{'_id':0,'id':1,'title':1,'score':{'$meta':'textScore'}}).limit(15)
        cursor = SteamStoreConfig.mongoCol.find(filter, fields).limit(maxResults)
        cursor.sort([('score', metaTextScore)])
        return cursor

