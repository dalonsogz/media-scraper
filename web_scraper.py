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
from bs4 import BeautifulSoup
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
    minTimeBtwRequest = 3
    maxTimeBtwRequest = 7
    maxProxyFails = 2
    minValidContenSizeBytes = 3000
    items = []
    processedItems = []
    notProcessedItems = []

    # Site parameters
    # totalNumItems = 0
    baseName = ""
    urlBase = ""
    itemDataFilePattern = ""
    destFilePath = ""
    mongoClient = ""
    mongoDb = ""
    mongoCol = ""

    # Lista de proxies (puede ser configurada leyendo de un archivo o directamente aquí)
    proxies_list = []
    proxies_file = ""

    def __init__(self):
        # Inicializa el contador de fallos por proxy
        self.proxy_fail_count = {}

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

    def load_proxies(self, filename="proxies.txt"):
        """
        Carga la lista de proxies desde un archivo (uno por línea).
        Ignora líneas vacías y líneas que empiezan por '#'.
        Formatos soportados:
        - http://ip:puerto
        - https://ip:puerto
        - socks4://ip:puerto
        - socks5://ip:puerto
        - ip:puerto (se asume http://)
        """
        self.proxies_file = filename
        proxies = []
        if os.path.exists(filename):
            with open(filename, 'r', encoding='utf8') as f:
                for line in f:
                    proxy = line.strip()
                    if not proxy or proxy.startswith('#'):
                        continue
                    if not (proxy.startswith("http://") or proxy.startswith("https://") or proxy.startswith("socks4://") or proxy.startswith("socks5://")):
                        proxy = "http://" + proxy
                    proxies.append(proxy)
        self.proxies_list = proxies
        self.proxy_fail_count = {proxy: 0 for proxy in proxies}

    def mark_failed_proxies(self):
        """
        Marca con '#' en proxies.txt los proxies que hayan fallado más de 5 veces en la ejecución.
        """
        if not os.path.exists(self.proxies_file):
            return
        # Obtener los proxies a marcar
        proxies_to_mark = set([p for p, count in self.proxy_fail_count.items() if count >= self.maxProxyFails])
        if not proxies_to_mark:
            return
        # Leer el archivo original
        with open(self.proxies_file, 'r', encoding='utf8') as f:
            lines = f.readlines()
        # Actualizar líneas
        new_lines = []
        for line in lines:
            lstr = line.strip()
            if not lstr or lstr.startswith('#'):
                new_lines.append(line)
                continue
            # Normalizar para comparar (añadir http:// si falta)
            norm = lstr
            if not (norm.startswith("http://") or norm.startswith("https://") or norm.startswith("socks4://") or norm.startswith("socks5://")):
                norm = "http://" + norm
            if norm in proxies_to_mark:
                if not lstr.startswith('#'):
                    new_lines.append('#' + line if not line.startswith('#') else line)
                else:
                    new_lines.append(line)
            else:
                new_lines.append(line)
        # Escribir el archivo actualizado
        with open(self.proxies_file, 'w', encoding='utf8') as f:
            f.writelines(new_lines)

    def common_requests(self, urlBase, i):
        url = urlBase + str(i)
        logger.info("Getting URL:{}".format(url))
        if not self.proxies_list:
            # Sin proxies, petición directa
            r = requests.get(url, headers=self.headers, verify=False)
            return r
        # Si hay proxies, intentar con cada uno de manera aleatoria
        proxies_to_try = self.proxies_list.copy()
        random.shuffle(proxies_to_try)
        last_exception = None
        for proxy in proxies_to_try:
            proxy_dict = {
                "http": proxy,
                "https": proxy
            }
            try:
                r = requests.get(url, headers=self.headers, verify=False, proxies=proxy_dict, timeout=10)
                if len(r.content) < self.minValidContenSizeBytes:
                    logger.warning(f"Proxy {proxy} respondió con contenido demasiado pequeño ({len(r.content)} bytes), se considera fallo.")
                    raise ValueError("Contenido demasiado pequeño")
                logger.info(f"Proxy OK: {proxy}")
                return r
            except Exception as e:
                self.proxy_fail_count[proxy] += 1
                logger.warning(f"Fallo [{self.proxy_fail_count[proxy]}] proxy {proxy}: {e}")
                if self.proxy_fail_count[proxy] >= self.maxProxyFails:
                    logger.warning(f"Proxy {proxy} superó el límite de fallos y será deshabilitado para esta ejecución y futuras.")
                    if proxy in self.proxies_list:
                        self.proxies_list.remove(proxy)
                    self.mark_failed_proxies()
                last_exception = e
        logger.error("Todos los proxies fallaron para la URL {}".format(url))
        raise RuntimeError("Todos los proxies fallaron")

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
            try:
                response = self.common_requests(self.urlBase, itemNumber)
            except RuntimeError as e:
                logger.error(f"Descarga detenida: {e}")
                raise SystemExit(1)
            self.process_response(response, itemNumber, item)
            self.write_item_processed(itemNumber)
            self.notProcessedItems.remove(itemNumber)
            time.sleep(random.randint(self.minTimeBtwRequest, self.maxTimeBtwRequest))
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
    (requestFiles.baseName, requestFiles.urlBase,
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

    # Cargar proxies
    requestFiles.load_proxies()

    # Dowload web data
    requestFiles.downloadItems(siteItem(), parseFrom, parseTo)

    # Parse web data and add to database
    if (parseTo - parseFrom) >= 0 and addToDatabase:
        parseItemFilesAndAddToDabase(requestFiles, parseFrom, parseTo)

def main():
    # Indexes between to start and stop downloading
    processFrom,processTo = 135684,144609
    dowloadAndParseItems(processFrom,processTo)

if __name__ == "__main__":
    main()
