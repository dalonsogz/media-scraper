import logging
import logging.config
import yaml
import random
import requests
import time
import urllib3
import re
import json
#from itemTheGamesDB import TheGamesDBConfig as siteCfg, TheGamesDBItem as siteItem, TheGamesDBMethods as siteMethods, TheGamesDBMongo as siteDB
from itemSteamStore import SteamStoreConfig as siteCfg, SteamStoreItem as siteItem, SteamStoreMethods as siteMethods, SteamStoreMongo as siteDB
from bs4 import BeautifulSoup

class RequestFiles:
    headers = {
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.81 Safari/537.36'}
    procesedItemsFile = "procesedItems.txt"
    maxTimeBtwRequest = 2
    items = []
    procesedItems = []
    notProcessedItems = []

    ########################## D O W N L O A D    I T E M S    S E C T I O N

    def read_items_processed(self):
        procesedItems = []
        try:
            with open(self.procesedItemsFile, 'r', encoding='utf8') as f:
                for line in f:
                    try:
                        procesedItems.append(int(line.strip()))
                    except ValueError:
                        pass
                # procesedItems = list(lines.split(" "))
        except FileNotFoundError:
            logger.error("Creating new '{}' file".format(self.procesedItemsFile))
        return procesedItems

    def write_item_processed(self, i):
        with open(self.procesedItemsFile, 'a', encoding='utf8') as f:
            f.write("{}\n".format(str(i)))

    def common_requests(self, urlBase, i):
        url = urlBase + str(i)
        logger.info("Getting URL:{}".format(url))
        r = requests.get(url, headers=self.headers, verify=False)
        return r

    def write_response_to_file(self, response, index):
        dataFile = self.itemDataFilePattern.format(str(index))
        with open(self.destFilePath + "/" + dataFile, 'wb') as fo:
            fo.write(response.content)

    def process_response(self, response, itemNumber, item):
        self.items.insert(item.id, item)
        self.write_response_to_file(response, itemNumber)

    def downloadItems(self, item, downloadfrom):
        totalItems = list(range(downloadfrom, self.totalNumItems + 1))
        self.procesedItems = self.read_items_processed()
        self.notProcessedItems = list(set(totalItems) - set(self.procesedItems))

        condition = len(self.notProcessedItems) > 0
        while condition:
            itemNumber = random.choice(self.notProcessedItems)
            logger.info("Item {}".format(str(itemNumber)))
            response = self.common_requests(self.urlBase, itemNumber)
            self.process_response(response, itemNumber, item)
            self.write_item_processed(itemNumber)
            self.notProcessedItems.remove(itemNumber)
            #            self.procesedItems.append(itemNumber)
            time.sleep(random.randint(0, self.maxTimeBtwRequest))
            condition = len(self.notProcessedItems) > 0

    ########################## P A R S E    I T E M S    S E C T I O N

    def parseHtml(self, index):
        dataFile = self.itemDataFilePattern.format(str(index))
        with open(self.destFilePath + "/" + dataFile, 'r', encoding='utf8') as fp:
            soup = BeautifulSoup(fp, "html.parser")

        return siteMethods.parseHtml(index, soup)


def init_logger():
    with open('config.yml', 'r') as f:
        config = yaml.safe_load(f.read())
        logging.config.dictConfig(config)
    return logging.getLogger()  # "web_scraper")


def downloadItems(downloadfrom):
    requestFiles = RequestFiles()
    requestFiles.totalNumItems, requestFiles.urlBase, requestFiles.itemDataFilePattern, requestFiles.destFilePath, requestFiles.mongoCol = siteCfg().config()
    requestFiles.downloadItems(siteItem(),downloadfrom)
    return requestFiles


def parseItemFilesAndAddToDabase(requestFiles, parseFrom):
    fails = []
    for itemIndex in range(parseFrom, requestFiles.totalNumItems + 1):
        try:
            item = requestFiles.parseHtml(itemIndex)
            requestFiles.items.append(item)
            jsonResult = siteMethods.toJson(item)
            logger.info("\n---------\n{}\n---------\n".format(json.dumps(jsonResult, sort_keys=True, indent=4)))
            requestFiles.mongoCol.insert_one(jsonResult)
        except FileNotFoundError as err:
            logger.warning(f"{itemIndex}\tNot found {err=}, {type(err)=}")
            fails.append(itemIndex)
        # except BaseException as err:
        #     logger.error(f"{itemIndex}\tUnexpected {err=}, {type(err)=}")
        #     fails.append(itemIndex)
        #     # raise
        except Exception as err:
            logger.error("Exception occurred", exc_info=True)
            fails.append(itemIndex)

    logger.warning("fails({}):{}".format(len(fails), fails))


global logger
flagAddToDatabase = True
parseFrom = 70
# parseFrom = 120879  #120318  #119378  #118333  #117574  #117059  #116473  #115817  #115268  #113640  #112645
#                     #111249  #110199  #109063  #107517  #106679  #105980  #105610  #105186  #104370  #103248

import keyboard

def main():
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    global logger
    logger = init_logger()

    requestFiles = downloadItems(parseFrom)

    if (requestFiles.totalNumItems-(parseFrom-1))>0 and flagAddToDatabase:
        parseItemFilesAndAddToDabase(requestFiles, parseFrom)

#    items = siteDB.findTitleSimilar("Inside",10)
#    for item in items:
#        print(item)

#    keyboard.wait()

if __name__ == "__main__":
    main()
