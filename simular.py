import sqlData as sql

def w_shingle(string, w):
    """Return (now a string) of the set of contiguous sequences (shingles) of `w` words
    in `string`."""
    # SOURCE: https://github.com/taravancil/w-shingle/blob/master/w_shingle.py
    words = string.split()
    num_words = len(words)

    # Confirm that 0 < `w` <= `num_words`
    if w > num_words or w == 0:
        raise Exception('Invalid argument -w')

    # If w is equal to the number of words in the input string, the
    # only item in the set is `words`.
    return [' '.join(words[i:i + w]) for i in range(len(words) - w + 1)]

"""
# compare each file to other files
print('Sample size', sample_size)
for i in range(len(filenames)):
    #print(filenames[i])
    random_sample_i = set(random.sample(index[i], sample_size))
    # random_sample_i = index[i]
    #print("Random sampling of 200: ", random_sample)
    for j in range(len(filenames)):
        random_sample_j = set(random.sample(index[j], sample_size))
        # random_sample_j = index[j]
        intersection = random_sample_i.intersection(random_sample_j)
        union = random_sample_i.union(random_sample_j)
        print(f"Jaccard {filenames[i]} to {filenames[j]}: ", len(intersection) / len(union))
"""

import math
from datasketch import MinHash, MinHashLSH, WeightedMinHashGenerator
from datasketch.experimental.aio.lsh import AsyncMinHashLSH

all_words = dict()
comments = []
transcripts = []

def calculate_shingle_weight(shingle):
    weight = 0.0
    words = shingle.split(' ')
    for word in words:
        if word in all_words:
            entry = all_words[word]
            weight += math.log2(
                (len(comments) + len(transcripts))
                /
                len(entry['documents'])
            )
    return weight

class File:
    def __init__(self, filename, isFile=False, contents=None, shingle_size=4):
        self.filename = filename
        if isFile:
            with open(filename, 'r') as fp:
                self.contents = fp.read()
        else:
            self.contents=contents
        self.shingles = w_shingle(self.contents, shingle_size)
        for shingle in self.shingles:
            words = shingle.split(' ')
            for word in words:
                if word in all_words:
                    all_words[word]['frequency'] += 1
                    all_words[word]['documents'].add(self.filename)
                else:
                    all_words[word] = dict()
                    all_words[word]['frequency'] = 1
                    all_words[word]['documents'] = set()
                    all_words[word]['documents'].add(self.filename)
        self.minhash = None

    def get_n_best_shingles(self, n=400):
        ret = [(calculate_shingle_weight(shingle), shingle) for shingle in self.shingles]
        ret = sorted(ret, key=lambda x: x[0], reverse=True)
        ret = [shingle[1] for shingle in ret]
        return ret[:n]

    def generate_minhash(self):
        self.minhash = MinHash(num_perm=400)
        for shingle in self.get_n_best_shingles(n=400):
            self.minhash.update(shingle.encode('utf8'))

"""
comments.append(File('data/8LSw3dkB52kComments.txt', shingle_size=2))
comments.append(File('data/9Ikknmv3DYgComments.txt', shingle_size=2))
comments.append(File('data/IuFPD8-0YDYComments.txt', shingle_size=2))
comments.append(File('data/cjzx7io_C5MComments.txt', shingle_size=2))
comments.append(File('data/nXO2T9rXGEIComments.txt', shingle_size=2))

transcripts.append(File('data/8LSw3dkB52kTranscript.txt', shingle_size=4))
transcripts.append(File('data/9Ikknmv3DYgTranscript.txt', shingle_size=4))
transcripts.append(File('data/IuFPD8-0YDYTranscript.txt', shingle_size=4))
transcripts.append(File('data/cjzx7io_C5MTranscript.txt', shingle_size=4))
transcripts.append(File('data/nXO2T9rXGEITranscript.txt', shingle_size=4))
"""


async def func():
    con = sql.connect_db('videoInfo.db')
    videos = sql.get_all_videos(con)
    for video in videos:
        video_id = video[0]
        if len(video[2].split(' ')) < 5 or len(video[3].split(' ')) < 5:
            print(f"Skipping over {video_id} for having a short comment or transcript")
            continue
        print("Inserted", video_id, "into memory")
        comments.append(File(video_id, contents=video[2]))
        transcripts.append(File(video_id, contents=video[3]))

    comment_lsh = await AsyncMinHashLSH(threshold=0.001, num_perm=400, storage_config={'type': 'aiomongo', 'mongo': {'host': 'localhost', 'port': 27017, 'db': 'comments_lsh'}})

    transcripts_lsh = await AsyncMinHashLSH(threshold=0.001, num_perm=400, storage_config={'type': 'aiomongo', 'mongo': {'host': 'localhost', 'port': 27017, 'db': 'transcripts_lsh'}})

    for comment in comments:
        print("Generating minhash for", comment.filename)
        comment.generate_minhash()
        await comment_lsh.insert(comment.filename, comment.minhash)

    for transcript in transcripts:
        print("Generating minhash for", transcript.filename)
        transcript.generate_minhash()
        await transcripts_lsh.insert(transcript.filename, transcript.minhash)


    for video_id in range(len(comments)):
        comment_result = await comment_lsh.query(comments[video_id].minhash)
        transcript_result = await transcripts_lsh.query(transcripts[video_id].minhash)

        #print(comments[video_id].filename, comments[video_id].get_n_best_shingles(n=10))
        print(comments[video_id].filename, comment_result)
        # print(comments[video_id].filename, transcripts[video_id].get_n_best_shingles(n=10))
        print(transcripts[video_id].filename, transcript_result)

        if len(comment_result) > 1:
            for other_video_id in comment_result:
                comment_minhash = [comment.minhash for comment in comments if comment.filename == other_video_id][0]
                print(comments[video_id].filename, other_video_id, comments[video_id].minhash.jaccard(comment_minhash))

        if len(transcript_result) > 1:
            for other_video_id in transcript_result:
                transcript_minhash = [transcript.minhash for transcript in transcripts if transcript.filename == other_video_id][0]
                print(transcripts[video_id].filename, other_video_id, transcripts[video_id].minhash.jaccard(transcript_minhash))

async def otherfunc():
    con = sql.connect_db('videoInfo3.db')
    videos = sql.get_all_videos(con)
    for video in videos:
        video_id = video[0]
        if len(video[2].split(' ')) < 5 or len(video[3].split(' ')) < 5:
            print(f"Skipping over {video_id} for having a short comment or transcript")
            continue
        print("Inserted", video_id, "into memory")
        comments.append(File(video_id, contents=video[2]))
        transcripts.append(File(video_id, contents=video[3]))

    lsh = await AsyncMinHashLSH(storage_config={'type': 'aiomongo', 'mongo': {'host': 'localhost', 'port': 27017, 'db': 'lsh_test'}}, threshold=0.01, num_perm=400)
    lsh_transcripts = await AsyncMinHashLSH(storage_config={'type': 'aiomongo', 'mongo': {'host': 'localhost', 'port': 27017, 'db': 'lsh_transcripts'}}, threshold=0.01, num_perm=400)
    for comment in comments:
        print("Generating minhash for", comment.filename)
        comment.generate_minhash()
        await lsh.insert(comment.filename, comment.minhash)

    for transcript in transcripts:
        print("Generating minhash for transcript", transcript.filename)
        transcript.generate_minhash()
        await lsh_transcripts.insert(transcript.filename, transcript.minhash)

    for video_id in range(len(comments)):
        print(f"Querying results for {videos[video_id][0]}")
        comment_result = await lsh.query(comments[video_id].minhash)
        transcript_result = await lsh_transcripts.query(transcripts[video_id].minhash)

        #print(comments[video_id].filename, comments[video_id].get_n_best_shingles(n=10))
        # print(comments[video_id].filename, comment_result)
        # print(comments[video_id].filename, transcripts[video_id].get_n_best_shingles(n=10))
        # print(transcripts[video_id].filename, transcript_result)

        if len(comment_result) > 1:
            for other_video_id in comment_result:
                if videos[video_id][0] == other_video_id:
                    continue
                comment_minhash = [comment.minhash for comment in comments if comment.filename == other_video_id][0]
                print("comment", comments[video_id].filename, other_video_id, comments[video_id].minhash.jaccard(comment_minhash))

        if len(transcript_result) > 1:
            for other_video_id in transcript_result:
                if videos[video_id][0] == other_video_id:
                    continue
                transcript_minhash = [transcript.minhash for transcript in transcripts if transcript.filename == other_video_id][0]
                print("transcript", transcripts[video_id].filename, other_video_id, transcripts[video_id].minhash.jaccard(transcript_minhash))

    await lsh.close()
    await lsh_transcripts.close()

import asyncio

loop = asyncio.new_event_loop()
loop.run_until_complete(otherfunc())
