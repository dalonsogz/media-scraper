import logging
import os

import requests
from concurrent.futures import ThreadPoolExecutor

PROXIES_FILE = "proxies.txt"
DEFAULT_SOURCES = [
    "https://raw.githubusercontent.com/clarketm/proxy-list/master/proxy-list-raw.txt",
    "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/http.txt",
]
HEALTHCHECK_URL = "https://thegamesdb.net/"
HEALTHCHECK_TIMEOUT = 5
HEALTHCHECK_WORKERS = 10


def normalizeProxy(proxy):
    proxy = (proxy or "").strip()
    if not proxy or proxy.startswith("#"):
        return None
    if "://" not in proxy:
        proxy = "http://" + proxy
    return proxy


def loadProxies(filename=PROXIES_FILE):
    proxies = []
    if not os.path.exists(filename):
        return proxies
    with open(filename, "r", encoding='utf8') as f:
        for line in f:
            proxy = normalizeProxy(line.strip())
            if proxy and proxy not in proxies:
                proxies.append(proxy)
    return proxies


def fetchProxiesFromSource(url, timeout=15):
    proxies = []
    r = requests.get(url, timeout=timeout)
    r.raise_for_status()
    try:
        data = r.json()
        entries = []
        if isinstance(data, list):
            entries = data
        elif isinstance(data, dict):
            for key in ("proxies", "data", "results", "items"):
                value = data.get(key)
                if isinstance(value, list):
                    entries = value
                    break
        for entry in entries:
            proxy = None
            if isinstance(entry, dict):
                for value in entry.values():
                    if isinstance(value, str) and ":" in value:
                        proxy = normalizeProxy(value)
                        break
            elif isinstance(entry, str):
                proxy = normalizeProxy(entry)
            if proxy and proxy not in proxies:
                proxies.append(proxy)
    except Exception:
        for line in r.text.splitlines():
            proxy = normalizeProxy(line)
            if proxy and proxy not in proxies:
                proxies.append(proxy)
    return proxies


def checkProxyHealth(proxy, url=HEALTHCHECK_URL, timeout=HEALTHCHECK_TIMEOUT):
    proxy_dict = {
        "http": proxy,
        "https": proxy
    }
    try:
        r = requests.get(url, proxies=proxy_dict, timeout=timeout, verify=False)
        return r.status_code == 200
    except Exception:
        return False


def renewProxies(filename=PROXIES_FILE, sources=DEFAULT_SOURCES):
    existingProxies = loadProxies(filename)
    newProxies = []
    for url in sources:
        try:
            fetchedProxies = fetchProxiesFromSource(url)
            newProxies.extend([p for p in fetchedProxies if p not in newProxies])
        except Exception as e:
            logging.error("Proxy renewal source failed {}: {}".format(url, e))
    mergedProxies = existingProxies + [p for p in newProxies if p not in existingProxies]
    # Health check concurrente de todos los candidatos (existentes + nuevos);
    # solo se conservan los proxies que responden correctamente
    with ThreadPoolExecutor(max_workers=HEALTHCHECK_WORKERS) as executor:
        health_checks = list(executor.map(lambda p: (p, checkProxyHealth(p)), mergedProxies))
    healthyProxies = [p for p, ok in health_checks if ok]
    with open(filename, 'w', encoding='utf8') as f:
        for proxy in healthyProxies:
            f.write("{}\n".format(proxy))
    logging.info("Proxy renewal finished. Total proxies: {} (healthy: {}).".format(len(healthyProxies), len(healthyProxies)))
    return healthyProxies


def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    mergedProxies = renewProxies()
    logging.info("Proxies renewed: {}".format(mergedProxies))


if __name__ == "__main__":
    main()
