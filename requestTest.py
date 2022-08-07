# Requests Quick Start
# https://docs.python-requests.org/en/latest/user/quickstart/ (removed)

# https://kennethreitz.org
# https://httpbin.org
# https://github.com/psf/requests
# https://docs.github.com/es/rest/activity/events


import requests

verbose = 1
logFile = "requesTest.log"
requesTest_reponse = "requesTest_reponse.json"
requesTest_reponse_full = "requesTest_reponse_full.json"
requesTest_reponse_gz = "requesTest_reponse_raw.gz"

def trace(self):
    if verbose > 0:
        print(self)

class RequestTest:

    log = trace

    def common_requests(self):
        r = requests.get('https://api.github.com/events')
        trace("GET:{0}".format(r));
        r = requests.post('https://httpbin.org/post', data = {'key':'value'})
        trace("POST:{0}".format(r));
        r = requests.put('https://httpbin.org/put', data = {'key':'value'})
        trace("PUT:{0}".format(r));
        r = requests.delete('https://httpbin.org/delete')
        trace("DELETE:{0}".format(r));
        r = requests.head('https://httpbin.org/get')
        trace("HEAD:{0}".format(r));
        r = requests.options('https://httpbin.org/get')
        trace("OPTIONS:{0}".format(r));
        payload = {'key1': 'value1', 'key2': 'value2'}
        r = requests.get('https://httpbin.org/get', params=payload)

    def pretty_print_response(self,resp):
        """
        At this point it is completely built and ready
        to be fired; it is "prepared".

        However pay attention at the formatting used in
        this function because it is programmed to be pretty
        printed and may differ from the actual request.
        """
        print('{}\n{}\r\n{}\r\n\r\n{}'.format(
            '-----------START-----------',
            resp.url,
            '\r\n'.join('{}: {}'.format(k, v) for k, v in resp.headers.items()),
            resp.content,
        ))

    def get_request(self,streamType):
        r = requests.get('https://api.github.com/events',stream=streamType)
        return r

    def read_response_raw(self,r):
#        r = requests.get('https://api.github.com/events', stream=True)
        trace(r.raw)
        # get the raw socket response from the server
        # does not transform the response content, access to the bytes as they were returned
        trace("Headers={}".format(r.headers))

        file = open(requesTest_reponse_gz, 'wb')
        file.write(r.raw.read(decode_content=False))  # .decode('iso8859-1'))
        file.close()

    def read_response(self,r):
#        r = requests.get('https://api.github.com/events')
        trace("url={}".format(r.url))
        trace("text={}".format(r.text))
        trace("json={}".format(r.json()))

        #  r.iter_content will automatically decode the gzip and deflate transfer-encodings
        with open(requesTest_reponse, 'wb') as fd:
            for chunk in r.iter_content(chunk_size=128):
                fd.write(chunk)

    def read_response_full(self,r):
#        r = requests.get('https://api.github.com/events', stream=True)
        self.pretty_print_response(r)
#        len(r.content)
        trace("Headers={}".format(r.headers))
        trace("Content-Type={} - Content-Length={}".format(r.headers['Content-Type'],r.headers['Content-Length']))

        # get the full response at once
        file=open(requesTest_reponse_full, 'wb')
        file.write(r.raw.read(r.headers['Content-Length'])) #.decode('iso8859-1'))
        file.write(r.content) #.decode('iso8859-1'))
        file.close()

    def get_file(self,urlBase,file):
        url = urlBase + file
        print("Getting URL:{}".format(url))
        r = requests.get(url, verify=False)
        fo = open(file, 'wb')
        fo.write(r.content)
        fo.close()

    def main(self):
        self.common_requests()

        httpResponse = self.get_request(True)
        self.read_response_raw(httpResponse)

        httpResponse = self.get_request(False)
        self.read_response(httpResponse)
        self.read_response_full(httpResponse)

#        self.get_file("https://www.pleasuredome.org.uk/images/","rotate.php")


def main():
    RequestTest().main()

if __name__ == "__main__":
    main()
