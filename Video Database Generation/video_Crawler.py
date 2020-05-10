#crawls youtube to populate a given count of videos given a seed link
from bs4 import BeautifulSoup
from urllib.request import urlopen
import json
import re

def scrape_vids(count, seed):
    videos = []
    url = seed
    seen = []
    while len(videos) < count:

        html = urlopen(url)
        page = BeautifulSoup(html, "html.parser")
        r = page.find_all('script')
        r2 = str(r[20])
        r3 = r2.split("'YPC_CAN_RATE_VIDEO': true,")[1]
        r4 = r3.split("'BG_P':")[0]
        for m in re.finditer('id=', r4):
            start = m.start() + 3
            end = start + 11
            id = r4[start: end]
            url = 'https://www.youtube.com/watch?v='+id
            if url not in videos and id not in seen:
                videos.append(url)
                seen.append(id)
    return videos


#     return videos
# if __name__ == "__main__":
#     scrape_vids(20,'https://www.youtube.com/watch?v=huTUOek4LgU')

