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
#it currently pulls from list of given urls, and uploads information to sqllite database
#TODO enable web crawl for 100s of vids, and ensure proper database structure


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
#

vids = VC.scrape_vids(count = 20, seed = "https://www.youtube.com/watch?v=4tyGM6r7t2I")

#https://www.youtube.com/watch?v=V61ai1qirgU
#vids = ["https://www.youtube.com/watch?v=8Bz5B1Y5yRc"]
print(vids)
print(len(vids))

#Main
for url in vids:

    #initialize video metadata
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    Video_ID = url.partition('v=')[2]
    url = url
    comments = ""
    transcript = ""

    videoInfoReq = youtube.videos().list(
        part="snippet",
        id="Ks-_Mh1QhMc"
    )
    videoInfo = videoInfoReq.execute()
    for item in videoInfo["items"]:
        upload_date = item["snippet"]["publishedAt"]
        channel = item["snippet"]["channelId"]
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    #Fetch, Parse and Export Trancript
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    final_Script = ""
    script, type =  FT.fetch(Video_ID)
    if type == 'generated':
        final_Script = FT.parse_auto(script)
    else:
        final_Script = FT.parse_manual(script)
    transcript = final_Script
    #FT.export(final_Script, Video_ID)  export to text file
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    #Fetch, Parse and Export Comments
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    raw = FC.extract_comments(Video_ID, url, youtube)
    final_Comments = FC.parse_comments(raw)
    comments = final_Comments
    #FC.export(final_Comments, Video_ID)   export to text file
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    #all data gathered succesfully, enter into database
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    if (Video_ID and url and comments and transcript and upload_date and channel):
        con = sql.connect_db(db_name)
        with con:
            cursor = sql.insert_video(con, Video_ID, url, comments, transcript, upload_date, channel)
            print("Succesfully added" + Video_ID + "to db")
    else:
        print("Missing fields for video ID" + Video_ID)
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~