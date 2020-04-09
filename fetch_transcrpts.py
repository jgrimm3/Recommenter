#Fetches youtube video transcripts
#videos stored as a list
#parsed and stripped of time stamps
#piped to text file stored named by Youtube ID
import re
from youtube_transcript_api import YouTubeTranscriptApi as YTScript

def fetch(Vid_ID):
    #load all possible scripts of a video
    possible_scripts = YTScript.list_transcripts(Vid_ID)
    #autogenerated seem to avoid repeats better at least for
    #'CKZ58bXtQnU'
    type = ''
    for scripts in possible_scripts:
        if scripts.is_generated:
            type = "generated"
            break
        else:
            type = "manual"

    autogenerated = possible_scripts.find_generated_transcript(['en'])
    script = autogenerated.fetch()
    return script, type

def parse_manual(script):
    parsed_script = ""
    for time_dictionary in script:
        parsed_script += " " + time_dictionary['text']
        # make all words lowercase
        text = parsed_script.lower()
        parsed_script = ""
        # use a regex to make any non alpha numeric chars a delimeter
        words = re.split(r"[^a-z0-9]", text)
        # remove spaces and blank lines
        for word in words:
            if len(word) >= 1:
                parsed_script += " " + word
    return parsed_script

def parse_auto(script):
    parsed_script = ""
    words = []
    for time_dictionary in script:
        parsed_script += " " + time_dictionary['text']
        # make all words lowercase
        text = parsed_script.lower()
        parsed_script = ""
        # use a regex to make any non alpha numeric chars a delimeter
        words = re.split(r"[^a-z0-9]", text)
        # remove spaces and blank lines
        for word in words:
            if len(word) >= 1:
                parsed_script += " " + word
    return parsed_script

def export(final_script, Vid_ID):
    f = open("data/"+ Vid_ID + "Transcript.txt", "w+")
    f.write(final_script)
    f.close()
