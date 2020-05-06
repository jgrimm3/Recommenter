# Recommenter
Custom Youtube recommendations based on video transcripts and video comments. Information Retrieval Project

#Dependencies

pip install utuby

pip install beautifulsoup4

pip install urllib

pip install youtube-transcript-api

pip install google-api-python-client

pip install google-auth-oauthlib

Pip install youtube-data-api

pip install datasketch

pip install rank-bm25

pip install openpyxl

pip install sklearn


Research Questions

Can we recommend videos solely off of youtube comments and transcripts?

How will these recommendations compare with Youtube?

How does this system scale?

Answers

Lessons Learned

Gathering data is difficult

Not all videos had comments allowed or transcripts. Oftentimes Movie Trailers or music videos disabled subtitles on their videos. This would mean no trailers or music videos can be successfully recommended in our current system. 

Github file size limit

Youtube rate limit extremely low
	
	Yotube doesnt specify if its related videos returned by its api are ranked

Future work

Learning to rank

