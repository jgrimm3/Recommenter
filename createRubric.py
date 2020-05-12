import os
import google_auth_oauthlib.flow
import googleapiclient.discovery
from youtube_api import YoutubeDataApi
from youtube_api import youtube_api_utils
import youtube_api.parsers as parser
from sklearn.metrics import ndcg_score
from openpyxl import Workbook
from openpyxl import load_workbook
import numpy as np
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

youtube = YoutubeDataApi('AIzaSyBL9Nzzvnwl_xPfXPKOCFTADEuHm70iH74')
youtubeRecommended = []
recommenterRecommended = []
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

#Pull top K videos from youtube API
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
def youtubeRecommender(ID, list):
    videoInfo = youtube.get_recommended_videos( video_id= ID, max_results=10, parser= parser.raw_json )
    for dict in videoInfo:
        for id, value in dict["id"].items():
           if id == 'videoId':
               list.append(value)
    return list
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

#Pull Top K videos from Recommenter
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
def recommenterRecommender(ID, list):


    return list

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

#Fill Excel Sheet
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
def fill_Excell(youRanks, recRanks):
    filename = "NDCG_Rubric.xlsx"
    workbook = Workbook()
    sheet = workbook.active
    sheet.column_dimensions['A'].width = 50
    sheet.cell(row=1, column=1).value = "Video Link"
    sheet.cell(row=1, column=2).value = "Rank 1 - 5"
    for row in range(2, 22):
        if row <= 11:
            sheet.cell(row=row, column=1).hyperlink = "https://www.youtube.com/watch?v=" + youRanks[row - 2]
            sheet.cell(row=row, column=1).style = "Hyperlink"
        else:
            ind = row - 11
            sheet.cell(row=row, column=1).hyperlink = "https://www.youtube.com/watch?v=" + recRanks[ind-1]
            sheet.cell(row=row, column=1).style = "Hyperlink"
    workbook.save(filename=filename)
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

def mainInput(inputURL):
#have to run first once to populate excel, then comment out until the input line to pull and uncomment below input line
    Video_ID = inputURL.partition('v=')[2]
    youtubeRecommended = youtubeRecommender(Video_ID, [])
    recommenterRecommended = youtubeRecommender(Video_ID, [])
    fill_Excell(youtubeRecommended, recommenterRecommended)

if __name__ == "__main__":
    mainInput('https://www.youtube.com/watch?v=zuGkNHnjo8s')