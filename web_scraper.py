import logging
import logging.config
import yaml
import random
import requests
import time
import urllib3
import re
import json
import os
from itemTheGamesdb import TheGamesDBConfig as siteCfg, TheGamesDBItem as siteItem, TheGamesDBMethods as siteMethods, TheGamesDBMongo as siteDB

# Debug flag to disable adding data to database
addToDatabase = True
# If the item index exists in database do not download
downloadIfExists = False
# If the item index exists do not add it to database
addIfExists = False


class RequestFiles:
    headers = {
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.81 Safari/537.36'}
    processedItemsFile = "processedItems_{}.txt"
    maxTimeBtwRequest = 2
    items = []
    processedItems = []
    notProcessedItems = []

    # Site parameters
    totalNumItems = 0
    baseName = ""
    urlBase = ""
    itemDataFilePattern = ""
    destFilePath = ""
    mongoClient = ""
    mongoDb = ""
    mongoCol = ""

    ########################## D O W N L O A D    I T E M S    S E C T I O N

    def read_items_processed(self):
        processedItems = []
        try:
            with open(self.processedItemsFile, 'r', encoding='utf8') as f:
                for line in f:
                    try:
                        processedItems.append(int(line.strip()))
                    except ValueError:
                        pass
                # processedItems = list(lines.split(" "))
        except FileNotFoundError:
            logger.error("Creating new '{}' file".format(self.processedItemsFile))
        return processedItems

    def write_item_processed(self, i):
        with open(self.processedItemsFile, 'a', encoding='utf8') as f:
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

    def downloadItems(self, item, downloadfrom, downloadto):
        totalItems = list(range(downloadfrom, downloadto + 1))
        self.processedItems = self.read_items_processed()
        self.notProcessedItems = list(set(totalItems))
        if not downloadIfExists:
            self.notProcessedItems = list(set(totalItems) - set(self.processedItems))

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


def init_logger(baseName):
    with open('config.yml', 'r') as f:
        config = yaml.safe_load(f.read())
        file_name, extension = os.path.splitext(config['handlers']['file']['filename'])
        config['handlers']['file']['filename'] = f"{file_name}_{baseName}{extension}"
        logging.config.dictConfig(config)
    return logging.getLogger()


def init_config():
    requestFiles = RequestFiles()
    (requestFiles.totalNumItems, requestFiles.baseName, requestFiles.urlBase,
     requestFiles.itemDataFilePattern, requestFiles.destFilePath, requestFiles.mongoCol) = siteCfg().config()
    requestFiles.processedItemsFile = requestFiles.processedItemsFile.format(requestFiles.baseName)
    return requestFiles


def parseItemFilesAndAddToDabase(requestFiles, parseFrom, parseTo):
    fails = []
    for itemIndex in range(parseFrom, parseTo + 1):
        try:
            results = list()
            if not addIfExists:
                results = list(requestFiles.mongoCol.find({"id": itemIndex}))

            if len(results) == 0:
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

    if len(fails) > 0:
        logger.warning("fails({}):{}".format(len(fails), fails))


def dowloadAndParseItems(parseFrom, parseTo):
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    requestFiles = init_config()
    global logger
    logger = init_logger(requestFiles.baseName)

    # Dowload web data
    requestFiles.downloadItems(siteItem(), parseFrom, parseTo)

    # Parse web data and add to database
    if (parseTo - parseFrom) >= 0 and addToDatabase:
        parseItemFilesAndAddToDabase(requestFiles, parseFrom, parseTo)

def main():
    # Indexes between to start and stop downloading
    processFrom,processTo = 120880, 121572
    dowloadAndParseItems(processFrom,processTo)

if __name__ == "__main__":
    main()
