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

    # Site parameterss
    #totalNumItems =    #131065 #2025-04-07     #130911 #2025-03-15     #130783 #2025-02-18
    #                   #130628 #2025-01-26     #130207 #2024-12-08     #129805 2024-10-13      #129173 #2024-09-14
                        #128539 #2024-08-11     #127793 #2024-07-07     #127108 #2024-06-08     #125963 #2024-04-27
                        #124599 #2024-03-22     #123892 #2024-03-01     #122663 #2024-01-23     #120879 #2023-11-18
                        #120317 #2023-10-28     #119378 #2023-09-23     #118332 #2023-09-02     #117573 #2023-08-11
                        #117058 #2023-07-22     #116472 #2023-07-08     #115816 #2023-06-16     #115266 #2023-06-02
                        #114677 #2023-05-21     #113639 #2023-04-25     #112644 #2023-04-02     #111248 #2023-03-13
                        #110198 #2023-02-19     #109062 #2023-02-04     #107516 #2022-12-24     #106678 #2022-11-26
                        #105979 #2022-11-04     #105609 #2022-10-22

    baseName = "thegamesdb"
    urlBase = "https://thegamesdb.net/game.php?id="
    itemDataFilePattern = "thegamesdb_{}.html"
    destFilePath = "thegamesdb"
    mongoClient = MongoClient(host="localhost", port=27017)
    mongoDb = mongoClient.thegamesdb
    mongoCol = mongoDb.items

    itemsMedia = ["Front Cover", "Back Cover", "Fanart", "Screenshot", "Banner", "Clearlogo"]
    itemYoutubeTrailer = "Trailer: YouTube"

    def config(self):
        return self.baseName, self.urlBase, self.itemDataFilePattern, self.destFilePath, self.mongoCol


class TheGamesDBItem:

    # Item data
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

    # Item control information
    date_added = ""
    date_updated = ""

    # Extra program flow data
    exists_in_database = False

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
        return[element for element in soup.find_all("div", class_="card-body") if not element.find("p", class_="game-overview")]

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

    def findItemDataTypes(soup):
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
        item.itemData = TheGamesDBMethods.findItemDataTypes(soup)
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

