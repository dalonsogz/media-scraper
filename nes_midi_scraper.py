# https://www.twilio.com/blog/web-scraping-and-parsing-html-in-python-with-beautiful-soup
import re
import string
import requests
from bs4 import BeautifulSoup


vgm_url = 'https://www.vgmusic.com/music/console/nintendo/nes/'
html_text = requests.get(vgm_url).text
soup = BeautifulSoup(html_text, 'html.parser')
valid_chars = "-_.() %s%s" % (string.ascii_letters, string.digits)

def download_track(count, track_element):
    # Get the title of the track from the HTML element
    track_title = track_element.text.strip().replace('/', '-')
    download_url = '{}{}'.format(vgm_url, track_element['href'])
    file_name = '{}_{}.mid'.format(count, track_title)
    file_name = ''.join(c for c in file_name if c in valid_chars)

    # Download the track
    r = requests.get(download_url, allow_redirects=True)
    with open(file_name, 'wb') as f:
        f.write(r.content)

    # Print to the console to keep track of how the scraping is coming along.
    print('Downloaded: {}'.format(track_title, download_url))


if __name__ == '__main__':
    attrs = {
        'href': re.compile(r'\.mid$')
    }

    tracks = soup.find_all('a', attrs=attrs, string=re.compile(r'^((?!\().)*$'))

    count = 0
    for track in tracks:
        print(track)
#        download_track(count, track)
        count += 1