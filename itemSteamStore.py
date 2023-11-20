import logging
import re
import json
from pymongo import MongoClient
from bson import SON as bson

class SteamStoreConfig:
    totalNumItems = 70

    urlBase = "https://store.steampowered.com/app/"
    itemDataFilePattern = "steampowered_{}.html"
    destFilePath = "steampowered"

    mongoClient = MongoClient(host="localhost", port=27017)
    mongoDb = mongoClient.steamstore
    mongoCol = mongoDb.items

    itemsMedia = ["Front Cover", "Back Cover", "Fanart", "Screenshot", "Banner", "Clearlogo"]
    itemYoutubeTrailer = "Trailer: YouTube"

    def config(self):
        return self.totalNumItems, self.urlBase, self.itemDataFilePattern, self.destFilePath, self.mongoCol


class SteamStoreItem:
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


class SteamStoreMethods:

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
            imgsLists.append(SteamStoreMethods.getHrefList(SteamStoreMethods.findImgType(soup, imgtype)))
        return imgsLists

    def findItemDataType(soup):
        return[element for element in soup.find_all("div", class_="card-body") if not element.find("p", class_="game-overview")]

    def getITemDataList(tags):
        items = []
        itemsClean = []
        for tag in tags:
            items.extend(tag.text.strip().split("\n"))
        items = list(filter(lambda x: (x != SteamStoreConfig.itemYoutubeTrailer), items))

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
        itemDataLists = SteamStoreMethods.getITemDataList(SteamStoreMethods.findItemDataType(soup))
        return itemDataLists

    def parseHtml(index, soup):
        item = SteamStoreItem()
        config = SteamStoreConfig()
        item.id = index
        item.title = SteamStoreMethods.findItemTitle(soup)
        item.description = SteamStoreMethods.findItemDescription(soup)
        item.trailer_link = SteamStoreMethods.findTrailerLink(soup)
        item.front_cover, item.back_cover, item.fanart, item.screenshot, item.banner, item.clearlogo = SteamStoreMethods.findImgTypes(
            soup, config.itemsMedia)
#        item.itemData = SteamStoreMethods.findItemDataTypes(soup)
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

