import fetch_transcrpts as FT
import fetch_comments as FC

#youtube api key AIzaSyBL9Nzzvnwl_xPfXPKOCFTADEuHm70iH74

#

videos = [
    #gaming
    #"https://www.youtube.com/watch?v=zaFdx5KR1Pw", #top games of 2020
    #"https://www.youtube.com/watch?v=IuFPD8-0YDY", #2020 and 2021
    #"https://www.youtube.com/watch?v=8LSw3dkB52k", #disapointing games

    #cooking
    #"https://www.youtube.com/watch?v=cjzx7io_C5M", #cooking hacks fake cuts
    #"https://www.youtube.com/watch?v=nXO2T9rXGEI", #pizza
    "https://www.youtube.com/watch?v=9Ikknmv3DYg", #sauce

]

for url in videos:
    Video_ID = url.partition('v=')[2]
    #Fetch, Parse and Export Trancript
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    final_Script = ""
    script, type =  FT.fetch(Video_ID)
    if type == 'generated':
        final_Script = FT.parse_auto(script)
    else:
        final_Script = FT.parse_manual(script)
    FT.export(final_Script, Video_ID)
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    #Fetch, Parse and Export Comments
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    raw = FC.load_all_comments(url)
    final_Comments = FC.parse_comments(raw)
    FC.export(final_Comments, Video_ID)