import sys
import random

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
    def __init__(self, filename, shingle_size=4):
        self.filename = filename
        with open(filename, 'r') as fp:
            self.contents = fp.read()
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

    def get_n_best_shingles(self, n=200):
        ret = [(calculate_shingle_weight(shingle), shingle) for shingle in self.shingles]
        ret = sorted(ret, key=lambda x: x[0], reverse=True)
        ret = [shingle[1] for shingle in ret]
        return ret[:n]

    def generate_minhash(self):
        self.minhash = MinHash(num_perm=300)
        for shingle in self.get_n_best_shingles(n=300):
            self.minhash.update(shingle.encode('utf8'))


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

comment_lsh = MinHashLSH(threshold=0.001, num_perm=300)
for comment in comments:
    comment.generate_minhash()
    comment_lsh.insert(comment.filename, comment.minhash)

transcripts_lsh = MinHashLSH(threshold=0.001, num_perm=300)
for transcript in transcripts:
    transcript.generate_minhash()
    transcripts_lsh.insert(transcript.filename, transcript.minhash)


for video_id in range(len(comments)):
    comment_result = comment_lsh.query(comments[video_id].minhash)
    transcript_result = transcripts_lsh.query(transcripts[video_id].minhash)

    print(comments[video_id].filename, comments[video_id].get_n_best_shingles(n=10))
    print(comments[video_id].filename, comment_result)
    print(comments[video_id].filename, transcripts[video_id].get_n_best_shingles(n=10))
    print(comments[video_id].filename, transcript_result)
