import re
import json


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
    totalNumItems = 1  # 94630
    urlBase = "https://thegamesdb.net/game.php?id="
    itemDataFilePattern = "thegamesdb_{}.html"
    destFilePath = "thegamesdb"

    itemsMedia = ["Front Cover", "Back Cover", "Fanart", "Screenshot", "Banner", "Clearlogo"]
    itemYoutubeTrailer = "Trailer: YouTube"

    def config(self):
        return self.totalNumItems, self.urlBase, self.itemDataFilePattern, self.destFilePath


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
        strItemData = json.dumps(item.itemData, default=lambda o: o.__dict__, indent=4).replace(
            "[\n    {", "").replace("\n    }\n]", "").replace("\n    {", "").replace("\n    },", ",")
#        print(json.dumps(item, default=lambda o: o.__dict__, indent=4) + "\n\n\n")
        strResult = re.sub("\"itemData\": \[[a-zA-z0-9\",:\-+\n {}]*}\n    \]", strItemData,
                           json.dumps(item, default=lambda o: o.__dict__, indent=4))
#        print(strResult + "\n\n\n")
        jsonResult = json.loads(strResult)
#        print("\n---------\n" + json.dumps(jsonResult, sort_keys=True, indent=4) + "\n---------\n")
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
