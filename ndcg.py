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

#Pull Excel Sheet
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
def pull_excelRanks():
    wb = load_workbook("NDCG_Rubric.xlsx")
    sheet = wb.active
    true_scores = []
    you_scores = []
    rec_scores = []
    for row in range(2, 21):
        if row <= 10:
            true_scores.append(int(sheet.cell(row=row, column=2).value))
            you_scores.append(int(sheet.cell(row=row, column=2).value))
        #else:
            #true_scores.append(int(sheet.cell(row=row, column=2).value))
            #rec_scores.append(sheet.cell(row=row, column=2).value)

    return true_scores, rec_scores, you_scores
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


#Eval NDCG
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
def calc_NDCG(true_scores, rec_scores, you_scores):
    true_relevance = np.asarray([true_scores])
    youtube_NDCG = ndcg_score(true_relevance, np.asarray([you_scores]), k=10)
    print("Ground Truth  "+ str(true_scores))
    print("Youtube Ranked  "+ str(you_scores))
    print("NDCG " + str(youtube_NDCG))
    #recommenter_NDCG = ndcg_score(true_relevance, rec_scores, k=10)

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

if __name__ == "__main__":
    true_scores, rec_scores, you_scores = pull_excelRanks()
    true_scores.sort(reverse= True)
    calc_NDCG(true_scores, rec_scores, you_scores)


