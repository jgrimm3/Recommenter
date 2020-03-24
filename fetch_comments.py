#Fetches youtube comments from videos
#videos stored as list for now
#comments parsed and piped to textfile with Name of youtube ID
import re
import os
import google_auth_oauthlib.flow
import googleapiclient.discovery

    #fCredits to https://stackoverflow.com/questions/36585824/how-to-get-all-comments-more-than-100-of-a-video-using-youtube-data-api-v3
def load_comments(match):
    all_comments = ""
    for item in match["items"]:
        comment = item["snippet"]["topLevelComment"]
        text = comment["snippet"]["textDisplay"]
        all_comments+= " " + text
        if 'replies' in item.keys():
            for reply in item['replies']['comments']:
                rtext = reply["snippet"]["textDisplay"]
                all_comments+= " " + text
    print(all_comments)
    return all_comments

def get_comment_threads(youtube, video_id):
    results = youtube.commentThreads().list(
        part="snippet",
        maxResults=100,
        order ='relevance',
        videoId=video_id,
        textFormat="plainText"
    ).execute()
    return results


def download_comments():
    # Disable OAuthlib's HTTPS verification when running locally.
    # *DO NOT* leave this option enabled in production.
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

    api_service_name = "youtube"
    api_version = "v3"
    DEVELOPER_KEY = "AIzaSyBL9Nzzvnwl_xPfXPKOCFTADEuHm70iH74"

    youtube = googleapiclient.discovery.build(
        api_service_name, api_version, developerKey=DEVELOPER_KEY)

    video_id = '9DzSGPad_z4'
    match = get_comment_threads(youtube, video_id)
    next_page_token = match["nextPageToken"]
    load_comments(match)


    # from utuby.utuby import youtube
    # utube = youtube(url)
    # print("Loaded")
    # raw_comments = utube.comments
    # print(raw_comments)

if __name__ == '__main__':
    comments = download_comments()


    #https://www.youtube.com/watch?v=DbyMpqPZ-K8
    #https: // www.youtube.com / watch?v = d0uFNajqTZI

