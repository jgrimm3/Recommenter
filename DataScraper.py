import fetch_transcrpts as FT
import fetch_comments as FC
import sqlData as sql
import os
import google_auth_oauthlib.flow
import googleapiclient.discovery

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


vids = [
    #gaming
    #"https://www.youtube.com/watch?v=zaFdx5KR1Pw", #top games of 2020
    #"https://www.youtube.com/watch?v=IuFPD8-0YDY", #2020 and 2021
    #"https://www.youtube.com/watch?v=8LSw3dkB52k", #disapointing games

    #cooking
    #"https://www.youtube.com/watch?v=cjzx7io_C5M", #cooking hacks fake cuts
    #"https://www.youtube.com/watch?v=nXO2T9rXGEI", #pizza
    "https://www.youtube.com/watch?v=9Ikknmv3DYg", #sauce
]

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
    raw = FC.load_all_comments(url)
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