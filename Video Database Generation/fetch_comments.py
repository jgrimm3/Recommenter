#Fetches youtube comments from videos
#videos stored as list for now
#comments parsed and piped to textfile with Name of youtube ID
import re
import os
import google_auth_oauthlib.flow
import googleapiclient.discovery
from utuby.utuby import youtube as yt

def extract_comments(id, url, youtube):
    count = count_comments(id, youtube)
    print(count)
    comments = ""
    #CHANGE THRESHOLD BELOW higher means longer scraping, lower means more chance of rate limit
    if int(count) > 20000:
        comments = partial_comments(youtube, part='snippet', videoId=id, order ='relevance', textFormat='plainText')
    else:
        comments = all_comments(url)
    return comments

def count_comments(id, youtube):
    count = 0
    request = youtube.videos().list(part="statistics", id=id)
    response = request.execute()
    for item in response["items"]:
        for stat, val in item['statistics'].items():
            if stat == "commentCount":
                count = val
    return count

def partial_comments(youtube, **kwargs):
    comments = []
    results = youtube.commentThreads().list(**kwargs).execute()

    while results:
        for item in results['items']:
            comment = item['snippet']['topLevelComment']['snippet']['textDisplay']
            comments.append(comment)
            #ParentId = item["id"]

            #replies too expensive rn
            # if (item['snippet']['totalReplyCount'] > 0):
            #     res2 = youtube.comments().list(part='snippet', parentId=ParentId, textFormat='plainText').execute()
            #     for item2 in res2['items']:
            #         replyText = item2['snippet']['textDisplay']
            #         comments.append(replyText)

        # Check if another page exists
        if 'nextPageToken' in results:
            kwargs['pageToken'] = results['nextPageToken']
            results = youtube.commentThreads().list(**kwargs).execute()
        else:
            break

    return comments

def all_comments(url):
    utube = yt(url)
    print("Loaded" + url)
    raw_comments = utube.comments
    return raw_comments

def parse_comments(comments):
    with open("stop_words.txt", 'r') as f:
         stop_words  = [line.rstrip('\n') for line in f]
    #print(stop_words)

    parsed_comments = ""
    words = []
    for comment in comments:
    # make all words lowercase
        text = comment.lower()
        # use a regex to make any non alpha numeric chars a delimeter
        words = re.split(r"[^a-z0-9]", text)
        # remove spaces and blank lines
        for word in words:
            if len(word) >= 1 and word not in stop_words:
                parsed_comments += " " + word
    return parsed_comments

def export(final_comments, Vid_ID):
    f = open("data/"+ Vid_ID + "Comments.txt", "w+")
    f.write(final_comments)
    f.close()
