import fetch_transcrpts as FT
import fetch_comments as FC

#youtube api key AIzaSyBL9Nzzvnwl_xPfXPKOCFTADEuHm70iH74



url = 'https: // www.youtube.com / watch?v = d0uFNajqTZI'
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
raw = FC.download_comments(url)
parsed = FC.parse_comments(raw)