import requests
import time

class RequestFiles:
    def common_requests(self,i):
        urlBase = 'https://www.pleasuredome.org.uk/forum_banners/'
        destFile = 'pleasuredome-forums-' + str(i) + '.gif'
        url = urlBase + destFile
        print("Getting URL:{}".format(url))
        r = requests.get(url, verify=False)
        fo = open(destFile, 'wb')
        fo.write(r.content)
        fo.close()

    def main(self):
        for i in range (1,102):
            self.common_requests(i)
            time.sleep(3)

def main():
    RequestFiles().main()

if __name__ == "__main__":
    main()
