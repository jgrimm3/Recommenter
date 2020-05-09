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
    true_vids = []
    you_scores = []
    you_vids = []
    rec_scores = []
    rec_vids = []
    for row in range(2, 22):
        if row <= 11:
            true_scores.append(int(sheet.cell(row=row, column=2).value))
            true_vids.append(str(sheet.cell(row=row, column=1).value))
            you_scores.append(int(sheet.cell(row=row, column=2).value))
            you_vids.append(str(sheet.cell(row=row, column=1).value))
        else:
            true_scores.append(int(sheet.cell(row=row, column=2).value))
            true_vids.append(str(sheet.cell(row=row, column=1).value))
            rec_scores.append(sheet.cell(row=row, column=2).value)
            rec_vids.append(str(sheet.cell(row=row, column=1).value))

    you_total = zip(you_scores, you_vids)
    rec_total = zip(rec_scores, rec_vids)
    true_total = zip(true_scores, true_vids)
    return true_total, rec_total, you_total
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


#Eval NDCG
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
def calc_NDCG(true_scores, rec_scores, you_scores):

    true_relevance = np.asarray([true_scores])
    youtube_NDCG = ndcg_score(true_relevance, np.asarray([you_scores]), k=10)
    recommenter_NDCG = ndcg_score(true_relevance, np.asarray([rec_scores]), k=10)
    print("Ground Truth  "+ str(true_scores))
    print("Youtube Ranked  "+ str(you_scores))
    print("NDCG " + str(youtube_NDCG))

    print("Youtube Ranked  " + str(rec_scores))
    print("NDCG " + str(recommenter_NDCG))
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

if __name__ == "__main__":
    true_total, rec_total, you_total = pull_excelRanks()
    sorted_true = sorted(true_total, key=lambda x: x[0], reverse= True)
    true_scores = [list(s) for s in zip(*sorted_true)][0][:10]
    true_Vids = [list(s) for s in zip(*sorted_true)][1][:10]

    you_scores = []
    for score,vid in you_total:
        if vid not in true_Vids:
            score = 0
        you_scores.append(score)

    rec_scores = []
    for score, vid in rec_total:

        if vid not in true_Vids:
            score = 0
        rec_scores.append(score)

    calc_NDCG(true_scores, rec_scores, you_scores)


