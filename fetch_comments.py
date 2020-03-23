#Fetches youtube comments from videos
#videos stored as list for now
#comments parsed and piped to textfile with Name of youtube ID



def download_comments(url):
    from utuby.utuby import youtube
    utube = youtube(url)

    print(youtube.coments)

def parse_comments(raw_comments):
    print(raw_comments)

if __name__ == '__main__':
    download_comments('https://www.youtube.com/watch?v=CKZ58bXtQnU')