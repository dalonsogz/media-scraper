import random
import requests
import time
import urllib3
import re
import json
from itemTheGamesDB import TheGamesDBConfig, TheGamesDBItem, TheGamesDBMethods
from bs4 import BeautifulSoup
from pymongo import MongoClient


class RequestFiles:
    headers = {
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.81 Safari/537.36'}
    procesedItemsFile = "procesedItems.txt"
    maxTimeBtwRequest = 5
    items = []
    procesedItems = []
    notProcessedItems = []

    totalNumItems = 0
    urlBase = ""
    itemDataFilePattern = ""
    destFilePath = ""

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
            print("Creating new '{}' file".format(self.procesedItemsFile))
        return procesedItems

    def write_item_processed(self, i):
        with open(self.procesedItemsFile, 'a', encoding='utf8') as f:
            f.write("{}\n".format(str(i)))

    def common_requests(self, urlBase, i):
        url = urlBase + str(i)
        print("Getting URL:{}".format(url))
        r = requests.get(url, headers=self.headers, verify=False)
        return r

    def write_response_to_file(self, response, index):
        dataFile = self.itemDataFilePattern.format(str(index))
        with open(self.destFilePath + "/" + dataFile, 'wb') as fo:
            fo.write(response.content)

    def process_response(self, response, itemNumber, item):
        self.items.insert(item.id, item)
        self.write_response_to_file(response, itemNumber)

    def downloadItems(self, item):
        totalItems = list(range(1, self.totalNumItems + 1))
        self.procesedItems = self.read_items_processed()
        self.notProcessedItems = list(set(totalItems) - set(self.procesedItems))

        condition = len(self.notProcessedItems) > 0
        while condition:
            itemNumber = random.choice(self.notProcessedItems)
            print("Item {}".format(str(itemNumber)))
            response = self.common_requests(self.urlBase, itemNumber)
            self.process_response(response, itemNumber, item)
            self.write_item_processed(itemNumber)
            self.notProcessedItems.remove(itemNumber)
            self.procesedItems.append(itemNumber)
            time.sleep(random.randint(0, self.maxTimeBtwRequest))
            condition = len(self.notProcessedItems) > 0

    ########################## P A R S E    I T E M S    S E C T I O N

    def parseHtml(self, index):
        dataFile = self.itemDataFilePattern.format(str(index))
        with open(self.destFilePath + "/" + dataFile, 'r', encoding='utf8') as fp:
            soup = BeautifulSoup(fp, "html.parser")

        return TheGamesDBMethods.parseHtml(index, soup)


def main():
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    requestFiles = RequestFiles()
    requestFiles.totalNumItems, requestFiles.urlBase, requestFiles.itemDataFilePattern, requestFiles.destFilePath = TheGamesDBConfig().config()
    #    requestFiles.downloadItems(TheGamesDBItem())

    mongoClient = MongoClient(host="localhost", port=27017)
    mongoDb = mongoClient.thegamesdb
    mongoCol = mongoDb.items

    fails = []
    for itemIndex in range(1, requestFiles.totalNumItems + 1):
        try:
            item = requestFiles.parseHtml(itemIndex)
            requestFiles.items.append(item)
            jsonResult = TheGamesDBMethods.toJson(item)
            print("\n---------\n" + json.dumps(jsonResult, sort_keys=True, indent=4) + "\n---------\n")
#            mongoCol.insert_one(item.toJson())
        except BaseException as err:
            print(f"{itemIndex}\tUnexpected {err=}, {type(err)=}")
            fails.append(itemIndex)
            raise

    print("fails({}):{}".format(len(fails), fails))


if __name__ == "__main__":
    main()
