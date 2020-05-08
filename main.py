#%%
import datasketch
from datasketch.experimental import AsyncMinHashLSH
from typing import List
import math
import sqlData as sql
import asyncio

SHINGLE_SIZE_COMMENTS = 2
SHINGLE_SIZE_TRANSCRIPT = 4

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

class VideoFromDB:
    def __init__(self, rows):
        self.id = rows[0]
        self.comment_content = rows[2]
        self.transcript_content = rows[3]

    def has_enough_comments(self) -> bool:
        return len(self.comment_content.split(' ')) >= SHINGLE_SIZE_COMMENTS

    def has_enough_transcripts(self) -> bool:
        return len(self.transcript_content.split(' ')) >= SHINGLE_SIZE_TRANSCRIPT

class LSHWrapper:

    def __init__(self, name):
        self.name = name
        self.lsh = None  # type: AsyncMinHashLSH
        pass

    @classmethod
    async def create(cls, name: str) -> 'LSHWrapper':
        self = LSHWrapper(name)
        self.lsh = await AsyncMinHashLSH(storage_config={'type': 'aiomongo', 'mongo': {'host': 'localhost', 'port': 27017, 'db': f"lsh_{name}"}}, threshold=0.01, num_perm=400)
        return self

    def query_from_video_id(self, video_id: str):
        # get minhash object
        pass

    async def query_from_minhash_obj(self, mh):
        result = await self.lsh.query(mh)
        return result

    async def insert_minhash_obj(self, mh_id, mh):
        print(f"Inserting {mh_id} into LSH {self.name}")
        await self.lsh.insert(mh_id, mh)

    async def close(self):
        await self.lsh.close()



class WordFrequency:
    def __init__(self, type="in_memory"):  # TODO: add support for networked index
        if type == "in_memory":
            self.index = dict()
            self.document_ids = set()
        else:
            print(f"WordFrequency type {type} not yet supported.")

    def add_to_index(self, word, doc_id):
        self.document_ids.add(doc_id)
        if word in self.index:
            entry = self.index[word]
            entry['frequency'] += 1
            entry['documents'].add(doc_id)
        else:
            self.index[word] = dict()
            entry = self.index[word]
            entry['frequency'] = 1
            entry['documents'] = set()
            entry['documents'].add(doc_id)

    def calculate_shingle_weight(self, shingle):
        weight = 0.0
        words = shingle.split(' ')
        for word in words:
            if word in self.index:
                entry = self.index[word]
                weight += math.log2(
                    len(self.document_ids)
                    /
                    len(entry['documents'])
                )
        return weight

    def sort_shingles(self, shingles: List[str]):
        ret = [(self.calculate_shingle_weight(shingle), shingle) for shingle in shingles]
        ret = sorted(ret, key=lambda x: x[0], reverse=True)
        ret = [shingle[1] for shingle in ret]
        return ret

class Recommenter:
    def __init__(self):
        global minhash_storage
        self.word_frequency = WordFrequency(type="in_memory")
        self.minhash_storage = minhash_storage  # todo: make this networked
        self.transcripts = None  # type: LSHWrapper
        self.comments = None  # type: LSHWrapper

    @classmethod
    async def create(cls):
        self = Recommenter()
        self.transcripts = await LSHWrapper.create(name="transcripts")
        self.comments = await LSHWrapper.create(name="comments")
        return self

    def readFromSQL(self, sqlitedb_path: str) -> List[VideoFromDB]:
        con = sql.connect_db(sqlitedb_path)
        videos = sql.get_all_videos(con)
        return [VideoFromDB(video) for video in videos]

    def store_minhash(self, key: str, minhash) -> None:
        self.minhash_storage[key] = minhash

    def retrieve_minhash(self, key: str):
        return self.minhash_storage.get(key, None)

    async def close(self):
        await self.comments.close()
        await self.transcripts.close()

# %%

async def populateDatabase():
    recommenter = await Recommenter.create()  # type: Recommenter
    videos = recommenter.readFromSQL("videoInfo3.db")[:1000]
    for video in videos:
        # first we add the video's words to our word frequency index
        print(f"Adding {video.id}'s words to word frequency index")
        for word in ' '.join([video.comment_content, video.transcript_content]).split(' '):
            recommenter.word_frequency.add_to_index(word, video.id)

    for video in videos:
        if video.has_enough_comments():
            print(f"Generating comment minhash for {video.id}")
            shingles = w_shingle(video.comment_content, SHINGLE_SIZE_COMMENTS)
            minhash = datasketch.MinHash(num_perm=400)
            for shingle in recommenter.word_frequency.sort_shingles(shingles)[:400]:
                minhash.update(shingle.encode('utf8'))
            minhash_id = f"{video.id}-comment"
            recommenter.store_minhash(minhash_id, minhash)
            await recommenter.comments.insert_minhash_obj(minhash_id, minhash)
        if video.has_enough_transcripts():
            print(f"Generating transcript minhash for {video.id}")
            shingles = w_shingle(video.transcript_content, SHINGLE_SIZE_TRANSCRIPT)
            minhash = datasketch.MinHash(num_perm=400)
            for shingle in recommenter.word_frequency.sort_shingles(shingles)[:400]:
                minhash.update(shingle.encode('utf8'))
            minhash_id = f"{video.id}-transcript"
            recommenter.store_minhash(minhash_id, minhash)
            await recommenter.transcripts.insert_minhash_obj(minhash_id, minhash)

    await recommenter.close()

# %%
async def queryDatabase(mh_id):
    recommenter = await Recommenter.create()  # type: Recommenter
    videos = recommenter.readFromSQL("videoInfo3.db")[:1000]
    for video in videos:
        test_minhash = recommenter.retrieve_minhash(f"{video.id}-comment")
        query_results = await recommenter.comments.query_from_minhash_obj(test_minhash)
        if len(query_results) > 0:
            print(video.id, query_results)
        test_minhash = recommenter.retrieve_minhash(f"{video.id}-transcript")
        query_results = await recommenter.transcripts.query_from_minhash_obj(test_minhash)
        if len(query_results) > 0:
            print(video.id, query_results)
    await recommenter.close()

# %%
minhash_storage = dict()  # Global Variable

# %%
loop = asyncio.new_event_loop()
# %%
loop.run_until_complete(populateDatabase())
# %%
loop.run_until_complete(queryDatabase('V4sWpLJcQoU-comment'))
