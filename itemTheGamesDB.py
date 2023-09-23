import logging
import re
import json
from pymongo import MongoClient
from bson import SON as bson

####<div class="card-body">
####<p>
# Platform: PC
# Region: Region Not Set
# Developer(s): Bungie | Gearbox Software
# Publishers(s): Microsoft Studios
# ReleaseDate: 2003-09-30
# Players: 66
# Co-op: Yes

####<div class="card-header">
####<h1>
# Título

####<div class="card-body">
####<p class="game-overview">
# Description:
####<p>
# Trailer: YouTube
# ESRB Rating: M - Mature 17+
# Genre(s): Action | Racing | Platform | Board | Family

class TheGamesDBConfig:
    totalNumItems = 119378 #2023-0923    118332 #2023-09-02    #117573 #2023-08-11    #117058 #2023-07-22    #116472 #2023-07-08
                        #115816 # 2023-06-16   #115266 #2023-06-02    #114677 #2023-05-21   #113639 #2023-04-25
                        #112644 #2023-04-02    #111248 #2023-03-13    #110198 #2023-02-19    #109062 #2023-02-04
                        #107516 #2022-12-24    #106678 #2022-11-26    #105979 #2022-11-04    #105609 #2022-10-22
    urlBase = "https://thegamesdb.net/game.php?id="
    itemDataFilePattern = "thegamesdb_{}.html"
    destFilePath = "thegamesdb"

    mongoClient = MongoClient(host="localhost", port=27017)
    mongoDb = mongoClient.thegamesdb
    mongoCol = mongoDb.items

    itemsMedia = ["Front Cover", "Back Cover", "Fanart", "Screenshot", "Banner", "Clearlogo"]
    itemYoutubeTrailer = "Trailer: YouTube"

    def config(self):
        return self.totalNumItems, self.urlBase, self.itemDataFilePattern, self.destFilePath, self.mongoCol


class TheGamesDBItem:
    id = 0
    title = ""
    description = ""
    trailer_link = ""

    itemData = []

    front_cover = ""
    back_cover = ""
    fanart = []
    screenshot = []
    banner = ""
    clearlogo = ""


class TheGamesDBMethods:

    def uncapitalize(s):
        return s[:1].lower() + s[1:]

    def toString(item):
        return "id:{}\ntitle:{}\ndescription:{}\ntrailerLink:{}\nitemData:{}\nfrontCover:{}\nbackCover:{}\nfanart:{}\nscreenshot:{}\nbanner:{}\nclearlogo:{}".format(
            item.id, item.title, item.description, item.trailer_link, item.itemData, item.front_cover, item.back_cover,
            item.fanart,
            item.screenshot, item.banner, item.clearlogo)

    def toJson(item):
        logging.debug("\n---------------------------------------------------------------------------------------------------------------------------------------\n")
        strJson = json.dumps(item, default=lambda o: o.__dict__, indent=4)
#        text = text.encode('unicode_escape').decode('utf-8')
#        text = re.sub(r'\\u(.){4}', '', text)
        logging.debug(strJson + "\n\n\n")
        strItemDataArray = json.dumps(item.itemData, default=lambda o: o.__dict__, indent=4)
        strItemDataList = strItemDataArray.replace("[\n    {", "").replace("\n    }\n]", "").replace("\n    {", "").replace("\n    },", ",")
        strItemDataList = strItemDataList.encode('unicode_escape').decode('utf-8')
        logging.debug(strItemDataList+"\n******************************\n")
        strJson = re.sub("\"itemData\":[\w\W]*}\n    \]",strItemDataList,strJson)
#        https://regex101.com/
        logging.debug(strJson + "\n\n\n")
        jsonResult = json.loads(strJson)
        logging.debug("\n---------\n" + json.dumps(jsonResult, sort_keys=True, indent=4) + "\n---------\n")
        logging.debug("\n---------------------------------------------------------------------------------------------------------------------------------------\n")
        return jsonResult

    def findItemTitle(soup):
        return soup.find("h1").text.strip()

    def findItemDescription(soup):
        return soup.find("p", class_="game-overview").text.strip()

    def findTrailerLink(soup):
        trailerLink = soup.find("a", {"data-caption": "Trailer"})
        if trailerLink:
            trailerLink = trailerLink.attrs['href']
        return trailerLink

    def findImgType(soup, imgtype):
        return soup.findAll("a", {"data-caption": re.compile(imgtype)})

    def getHrefList(tags):
        return list("".join(tag.attrs['href']) for tag in (tags))

    def findImgTypes(soup, imgTypeList):
        imgsLists = []
        for imgtype in imgTypeList:
            imgsLists.append(TheGamesDBMethods.getHrefList(TheGamesDBMethods.findImgType(soup, imgtype)))
        return imgsLists

    def findItemDataType(soup):
        return soup.findAll("div", class_="card-body")

    def getITemDataList(tags):
        items = []
        itemsClean = []
        for tag in tags:
            items.extend(tag.text.strip().split("\n"))
        items = list(filter(lambda x: (x != TheGamesDBConfig.itemYoutubeTrailer), items))

        for indexitem, item in enumerate(items):
            if ":" not in item:
                # items.remove(item)
                continue
            if "(s):" in item:
                values = re.split(':|\|', item)
                for indexval, value in enumerate(values):
                    values[indexval] = value.strip()
                dictItem = {values[0].replace("(s)", "").replace(" ","_").lower(): values[1:]}
                itemsClean.append(dictItem)
            else:
                listItem = item.split(":")
                dictItem = {listItem[0].strip().replace(" ","_").lower(): listItem[1].strip()}
                itemsClean.append(dictItem)
        return itemsClean

    def findiItemDataTypes(soup):
        itemDataLists = TheGamesDBMethods.getITemDataList(TheGamesDBMethods.findItemDataType(soup))
        return itemDataLists

    def parseHtml(index, soup):
        item = TheGamesDBItem()
        config = TheGamesDBConfig()
        item.id = index
        item.title = TheGamesDBMethods.findItemTitle(soup)
        item.description = TheGamesDBMethods.findItemDescription(soup)
        item.trailer_link = TheGamesDBMethods.findTrailerLink(soup)
        item.front_cover, item.back_cover, item.fanart, item.screenshot, item.banner, item.clearlogo = TheGamesDBMethods.findImgTypes(
            soup, config.itemsMedia)
        item.itemData = TheGamesDBMethods.findiItemDataTypes(soup)
        return item


class TheGamesDBMongo:

    @classmethod
    def findTitleSimilar(self,title,maxResults):
        metaTextScore = bson({'$meta': 'textScore'})
        filter = bson({'$text': {'$search': title}}) #, 'platform': 'PC' })
        fields = bson({'_id': 0, 'id': 1, 'title': 1, 'platform': 1, 'score': metaTextScore})
        # query: {"$text": {"$search": title}},{'_id':0,'id':1,'title':1,'score':{'$meta':'textScore'}}).limit(15)
        cursor = TheGamesDBConfig.mongoCol.find(filter, fields).limit(maxResults)
        cursor.sort([('score', metaTextScore)])
        return cursor

