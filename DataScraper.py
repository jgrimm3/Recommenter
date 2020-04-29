import fetch_transcrpts as FT
import fetch_comments as FC
import sqlData as sql
import video_Crawler as VC
import os
import google_auth_oauthlib.flow
import googleapiclient.discovery
from urllib.request import urlopen
from bs4 import BeautifulSoup


#README
#This file will be the main data gathering tool, it will crawl youtube links, and populate database info with the folloewing:
#youtube video ID, url, channel id, upload date, parsed transcript and parsed comments
#it currently pulls from scraped URLS for a givven seed, and uploads information to sqllite database


#yk AIzaSyBL9Nzzvnwl_xPfXPKOCFTADEuHm70iH74#
# Disable OAuthlib's HTTPS verification when running locally.
# *DO NOT* leave this option enabled in production.
os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

api_service_name = "youtube"
api_version = "v3"
DEVELOPER_KEY = "AIzaSyBL9Nzzvnwl_xPfXPKOCFTADEuHm70iH74"
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
youtube = googleapiclient.discovery.build(
    api_service_name, api_version, developerKey=DEVELOPER_KEY)

db_name = 'videoInfo.db'
#https://www.youtube.com/watch?v=B-yhF7IScUE movies


#next   https://www.youtube.com/watch?v=UVS1T8OueFM
seed = "https://www.youtube.com/watch?v=uFHqDcu88bg"
vids = VC.scrape_vids(count = 35, seed = seed)


print(vids)
print(len(vids))

con = sql.connect_db(db_name)
results = sql.get_Video_ids(con)
ALREADY_SEEN = [value for value, in results]
total_Stored = len(ALREADY_SEEN)
print(total_Stored)
count = 0

#Main
for url in vids:

    #initialize video metadata
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    Video_ID = url.partition('v=')[2]
    if Video_ID in ALREADY_SEEN:
        print("Seen Video Already")
        continue
    url = url
    comments = ""
    transcript = ""
    cont = vids.index(url) + 1
    print("processing  " + Video_ID, cont, len(vids))
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    #Fetch, Parse and Export Trancript
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    final_Script = ""
    try:
        script, type =  FT.fetch(Video_ID)
    except:
        print("trancript error, skipping "+ Video_ID)
        continue
    if type == 'generated':
        final_Script = FT.parse_auto(script)
    else:
        final_Script = FT.parse_manual(script)
    transcript = final_Script
    #FT.export(final_Script, Video_ID)  export to text file
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    #Fetch, Parse and Export Comments
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    try:
        raw = FC.extract_comments(Video_ID, url, youtube)
    except:
        print("comment error, skipping "+ Video_ID)
        continue
    final_Comments = FC.parse_comments(raw)
    comments = final_Comments
    #FC.export(final_Comments, Video_ID)   export to text file
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    videoInfoReq = youtube.videos().list(
        part="snippet",
        id=Video_ID
    )
    videoInfo = videoInfoReq.execute()
    for item in videoInfo["items"]:
        upload_date = item["snippet"]["publishedAt"]
        channel = item["snippet"]["channelId"]
    print("Succesfull ", count, cont)

    #all data gathered succesfully, enter into database
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    if (Video_ID and url and comments and transcript and upload_date and channel):
        con = sql.connect_db(db_name)
        with con:
            cursor = sql.insert_video(con, Video_ID, url, comments, transcript, upload_date, channel)
            print("Succesfully added" + Video_ID + " to db")
            count +=1

    else:
        print("Missing fields for video ID " + Video_ID)
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~