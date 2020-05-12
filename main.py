#%%
import datasketch
from datasketch.experimental import AsyncMinHashLSH
from typing import List, Tuple, Dict
import math
import sqlData as sql
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from tqdm import tqdm
from pymongo import UpdateOne
import base64
import json
import datetime

SHINGLE_SIZE_COMMENTS = 2
SHINGLE_SIZE_TRANSCRIPT = 3

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
        return len(self.comment_content.split(' ')) >= (SHINGLE_SIZE_COMMENTS + 2)

    def has_enough_transcripts(self) -> bool:
        return len(self.transcript_content.split(' ')) >= (SHINGLE_SIZE_TRANSCRIPT + 2)

class LSHWrapper:

    def __init__(self, name):
        self.name = name
        self.lsh = None  # type: AsyncMinHashLSH
        pass

    @classmethod
    async def create(cls, name: str) -> 'LSHWrapper':
        self = LSHWrapper(name)
        self.lsh = await AsyncMinHashLSH(storage_config={'type': 'aiomongo', 'mongo': {'host': '127.0.0.1', 'port': 27017, 'db': f"lsh_{name}_800_w2"}}, threshold=0.01, num_perm=800)
        return self

    async def query_from_minhash_obj(self, mh):
        result = await self.lsh.query(mh)
        return result

    async def insert_minhash_obj(self, mh_id, mh):
        print(f"Inserting {mh_id} into LSH {self.name}")
        await self.lsh.insert(mh_id, mh)

    async def has_key(self, key):
        print(f"Checking to see if {key} in LSH {self.name}")
        return (await self.lsh.has_key(key))

    async def close(self):
        await self.lsh.close()


class MinHashStorage:
    def __init__(self):
        self.client = AsyncIOMotorClient('127.0.0.1', 27017)
        self.db = self.client.get_database('min_hash_storage_w2')
        self.hashes_collection = self.db.get_collection('hashes')
        pass

    @classmethod
    async def create(cls) -> 'MinHashStorage':
        self = MinHashStorage()
        return self

    async def store_hash(self, mh_id: str, mh: datasketch.MinHash):
        """
        Note, this will be saved as a LeanMinHash.
        :param mh_id:
        :param mh:
        :return:
        """
        lean_mh = datasketch.LeanMinHash(mh) # converts minhash into lean minash
        buf = bytearray(lean_mh.bytesize()) # create buf that we will upload to mongo
        lean_mh.serialize(buf) # serializes lean mh into the buffer
        base64_bytes = base64.b64encode(buf)
        await self.hashes_collection.update_one({'mh_id': mh_id}, {'$set': {'base64_bytes': base64_bytes}}, upsert=True)

    async def retrieve_hash(self, mh_id: str) -> datasketch.LeanMinHash:
        """
        Note.
        :param mh_id:
        :return: None if not stored
        """
        doc = await self.hashes_collection.find_one({'mh_id': mh_id})
        if doc is None:
            return None
        base64_bytes = doc['base64_bytes']
        buf = bytearray(base64.b64decode(base64_bytes))
        lean_mh = datasketch.LeanMinHash.deserialize(buf)
        return lean_mh


class WordFrequency:
    def __init__(self, type="in_memory"):
        self.has_cache = False
        self.unique_doc = None
        self.word_entries = dict()
        self.type = type
        if self.type == "in_memory":
            self.index = dict()
            self.document_ids = set()
        elif self.type == "mongo":
            self.client = AsyncIOMotorClient('127.0.0.1', 27017)
            self.db = self.client.get_database('word_frequency')
            self.words_collection = self.db.get_collection('words')
            self.misc_collection = self.db.get_collection('misc')
        else:
            print(f"WordFrequency type {self.type} not yet supported.")

    async def initialize(self):  # only call on mongo
        self.unique_doc = await self.misc_collection.find_one({'purpose': 'doc_ids'})
        if self.unique_doc is None:
            await self.misc_collection.insert_one({'purpose': 'doc_ids', 'doc_ids': []})
            self.unique_doc = await self.misc_collection.find_one({'purpose': 'doc_ids'})

    async def build_cache(self):
        self.unique_doc = await self.misc_collection.find_one({'purpose': 'doc_ids'})
        self.word_entries = dict()
        print("Building word cache...")
        for entry in (await self.words_collection.find().to_list(100000)):  # limit not working
            self.word_entries[entry['word']] = entry
        print(f"Number of words in cache {len(self.word_entries)}")
        self.has_cache = True

    async def upload_cache(self):
        if self.has_cache is False:
            return
        print("Generating operations to update word entries...")
        operations = []
        for word, entry in tqdm(self.word_entries.items()):
            if 'dirty' in entry and entry['dirty'] is True:
                entry['dirty'] = False
                operations.append(UpdateOne({'word': entry['word']}, {'$set': entry}, upsert=True))
                # await self.words_collection.update_one({'word': entry['word']}, {'$set': entry}, upsert=True)
        if len(operations) > 0:
            print(f"Submitting bulk write request with {len(operations)} update operations...")
            await self.words_collection.bulk_write(operations, ordered=False)
        else:
            print("Had no ops to upload")
        print("Deleted word cache")
        print("Updating doc_ids")
        self.words_entries = dict()
        self.has_cache = False
        await self.misc_collection.update_one({'purpose': 'doc_ids'}, { '$set': {'doc_ids': self.unique_doc['doc_ids']}})

    async def add_to_index(self, word, doc_id):
        if self.type == "in_memory":
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
        elif self.type == "mongo":
            if self.has_cache is False:
                await self.build_cache()
            if word in self.word_entries:  # word is in our cache
                entry = self.word_entries[word]
                entry['frequency'] += 1
                if doc_id not in entry['documents']:
                    entry['documents'].append(doc_id)
                entry['dirty'] = True
            else:
                # check if an entry exists but is not in cache
                current_entry = await self.words_collection.find_one(filter={'word': word})
                frequency = 0
                documents = []
                if current_entry is not None:
                    frequency = current_entry['frequency']
                    documents = current_entry['documents']
                if doc_id not in documents:
                    documents.append(doc_id)
                frequency += 1
                # add to our cache
                self.word_entries[word] = {'word': word, 'frequency': frequency, 'documents': documents, 'dirty': True}

    async def add_doc_id(self, doc_id):
        if doc_id not in self.unique_doc['doc_ids']:
            self.unique_doc['doc_ids'].append(doc_id)

    async def calculate_shingle_weight(self, shingle):
        weight = 0.0
        words = shingle.split(' ')
        for word in words:
            if self.type == "in_memory":
                if word in self.index:
                    entry = self.index[word]
                    weight += math.log2(
                        len(self.document_ids)
                        /
                        len(entry['documents'])
                    )
            elif self.type == "mongo":
                if self.has_cache is False:
                    await self.build_cache()
                # find entry in our cache
                entry = self.word_entries.get(word, None)
                if entry is None: # find it in our db
                    pass # entry = await self.words_collection.find_one(filter={'word': word})
                if entry is not None and entry['frequency'] > 1:
                    weight += math.log2(
                        len(self.unique_doc['doc_ids'])
                        /
                        len(entry['documents'])
                    )
                else:
                    pass
                    #weight += math.log2(
                    #    len(self.unique_doc['doc_ids'])
                    #    /
                    #    10
                    #)
        return weight

    async def sort_shingles(self, shingles: List[str]):
        print(f"Sorting {len(shingles)} shingles")
        ret = []
        for shingle in tqdm(shingles):
            ret.append((await self.calculate_shingle_weight(shingle), shingle))
        #ret = [(await self.calculate_shingle_weight(shingle), shingle) for shingle in shingles]
        ret = sorted(ret, key=lambda x: x[0], reverse=True)
        ret = [shingle[1] for shingle in ret]
        return ret

class Recommenter:
    def __init__(self):
        self.word_frequency = WordFrequency(type="mongo")
        self.minhash_storage = None  # type: MinHashStorage
        self.transcripts = None  # type: LSHWrapper
        self.comments = None  # type: LSHWrapper

    @classmethod
    async def create(cls):
        self = Recommenter()
        self.minhash_storage = await MinHashStorage.create()
        self.transcripts = await LSHWrapper.create(name="transcripts")
        self.comments = await LSHWrapper.create(name="comments")
        await self.word_frequency.initialize()
        return self

    async def get_related_videos(self, vid_id: str) -> Dict[str, Dict[str, float]]:
        results = {}  # type: Dict[str, Dict[str, float]]
        comment_mh_id = f"{vid_id}-comment"
        comment_mh = await self.minhash_storage.retrieve_hash(comment_mh_id)
        if comment_mh is not None:
            related_comments = await self.comments.query_from_minhash_obj(comment_mh)  # type: List[str]
            # get min hashes for results
            # print(related_comments)
            for mh_id in related_comments:
                if mh_id == f"{vid_id}-comment":
                    continue
                retrieved = await self.minhash_storage.retrieve_hash(mh_id)
                if retrieved is not None:
                    vid_id = mh_id.split('-')[0]
                    if vid_id not in results:
                        results[vid_id] = {}
                    results[vid_id]['comment'] = comment_mh.jaccard(retrieved)
        transcript_mh_id = f"{vid_id}-transcript"
        transcript_mh = await self.minhash_storage.retrieve_hash(transcript_mh_id)
        if transcript_mh is not None:
            related_transcripts = await self.transcripts.query_from_minhash_obj(transcript_mh)  # type: List[str]
            print(related_transcripts)
            for mh_id in related_transcripts:
                if mh_id == f"{vid_id}-transcript":
                    continue
                retrieved = await self.minhash_storage.retrieve_hash(mh_id)
                if retrieved is not None:
                    vid_id = mh_id.split('-')[0]
                    if vid_id not in results:
                        results[vid_id] = {}
                    results[vid_id]['transcript'] = transcript_mh.jaccard(retrieved)
        if comment_mh is None and transcript_mh is None:
            print(f"Sorry, did not have {vid_id} in the system.")
        return results

    def readFromSQL(self, sqlitedb_path: str) -> List[VideoFromDB]:
        con = sql.connect_db(sqlitedb_path)
        videos = sql.get_all_videos(con)
        return [VideoFromDB(video) for video in videos]

    async def store_minhash(self, key: str, minhash) -> None:
        await self.minhash_storage.store_hash(key, minhash)

    async def retrieve_minhash(self, key: str) -> datasketch.LeanMinHash:
        return (await self.minhash_storage.retrieve_hash(key))

    async def close(self):
        await self.comments.close()
        await self.transcripts.close()
        await self.word_frequency.upload_cache()


async def populateDatabase():
    recommenter = await Recommenter.create()  # type: Recommenter
    videos = recommenter.readFromSQL("videoInfo4.db")

    """
    i = 0
    for video in videos:
        # first we add the video's words to our word frequency index
        if video.id in recommenter.word_frequency.unique_doc['doc_ids']:
            print(f"Not adding {video.id}'s words to word frequency index, already indexed")
            continue
        else:
            print(f"Adding {video.id}'s words to word frequency index")
            for word in tqdm(' '.join([video.comment_content, video.transcript_content]).split(' ')):
                await recommenter.word_frequency.add_to_index(word, video.id)
            await recommenter.word_frequency.add_doc_id(video.id)
            if i == 10:
                await recommenter.word_frequency.upload_cache()
                i = -1
            i += 1
    
    """
    for video in videos:
        if video.id in ["5DGwOJXSxqg", "mWXurqWRA74", "jkGtMjkkmn4", "cqkiim_K0sc", "Ft00DUHRCOo", "FtX_oGO9MHo"]:
            print(f"Skipping {video.id} as its on the blacklist")
            continue
        """
        if video.has_enough_comments():
            minhash_id = f"{video.id}-comment"
            if (await recommenter.retrieve_minhash(minhash_id)) != None:
                print(f"Skipping video {video.id} because comment minhash stored, presumed already indexed")
                continue # skip video
            print(f"Generating comment minhash for {video.id}")
            shingles = w_shingle(video.comment_content, SHINGLE_SIZE_COMMENTS)
            minhash = datasketch.MinHash(num_perm=800)
            rated_shingles = await recommenter.word_frequency.sort_shingles(shingles)
            print(f"Top 4 comment shingles for {video.id} are {rated_shingles[:4]}")
            for shingle in rated_shingles[:800]:
                minhash.update(shingle.encode('utf8'))
            print(f"Storing minhash {minhash_id}")
            await recommenter.store_minhash(minhash_id, minhash)
            #print(f"Inserting minhash {minhash_id}")
            #await recommenter.comments.insert_minhash_obj(minhash_id, minhash)
        """
        if video.has_enough_transcripts():
            minhash_id = f"{video.id}-transcript-w{SHINGLE_SIZE_TRANSCRIPT}"
            if (await recommenter.retrieve_minhash(minhash_id)) != None:
                print(f"Skipping video {video.id} because transcript minhash stored, presumed already indexed.")
                continue # skip video
            print(f"Generating transcript minhash for {video.id}")
            shingles = w_shingle(video.transcript_content, SHINGLE_SIZE_TRANSCRIPT)
            minhash = datasketch.MinHash(num_perm=800)
            rated_shingles = await recommenter.word_frequency.sort_shingles(shingles)
            print(f"Top 4 transcript shingles for {video.id} are {rated_shingles[:4]}")
            for shingle in rated_shingles[:800]:
                minhash.update(shingle.encode('utf8'))
            print(f"Storing minhash {minhash_id}")
            await recommenter.store_minhash(minhash_id, minhash)
            #print(f"Inserting minhash {minhash_id}")
            #await recommenter.transcripts.insert_minhash_obj(minhash_id, minhash)

    await recommenter.close()

async def debugvid():
    recommenter = await Recommenter.create()  # type: Recommenter
    videos = recommenter.readFromSQL("videoInfo3.db")[:1000]
    for video in videos:
        if video.id in ["5DGwOJXSxqg", "mWXurqWRA74"]:
            print(f"Generating comment minhash for {video.id}")
            shingles = w_shingle(video.comment_content, SHINGLE_SIZE_COMMENTS)
            minhash = datasketch.MinHash(num_perm=800)
            rated_shingles = await recommenter.word_frequency.sort_shingles(shingles)
            print(f"Top 4 comment shingles for {video.id} are {rated_shingles[:4]}")
            for shingle in rated_shingles[:800]:
                minhash.update(shingle.encode('utf8'))
            minhash_id = f"{video.id}-comment"
            print(f"Storing minhash {minhash_id}")
            await recommenter.store_minhash(minhash_id, minhash)
            print(f"Inserting minhash {minhash_id}")
            await recommenter.comments.insert_minhash_obj(minhash_id, minhash)


async def queryDatabase():
    recommenter = await Recommenter.create()  # type: Recommenter
    videos = recommenter.readFromSQL("videoInfo4.db")
    """
    for video in videos:
        results = await recommenter.get_related_videos(video.id)
        if len(results) > 0:
            print(f"Queried {video.id}")
            print(results)
    """
    # results = await recommenter.get_related_videos("p40OetppIDg")
    # print(results)
    mh1 = await recommenter.retrieve_minhash("p40OetppIDg-transcript")
    print(await recommenter.transcripts.lsh.query(mh1))
    #mh2 = await recommenter.retrieve_minhash("RoompSKVq6w-transcript")
    #print(mh1.jaccard(mh2))
    await recommenter.close()

async def brutesearch():
    recommenter = await Recommenter.create()  # type: Recommenter
    videos = recommenter.readFromSQL("videoInfo4.db")
    minhashes = {}
    comment_lsh = datasketch.MinHashLSH(threshold=0.7, num_perm=800)
    transcript_lsh = datasketch.MinHashLSH(threshold=0.4, num_perm=800)
    print("Adding videos to lsh")
    for video in tqdm(videos):
        comment_mh = await recommenter.retrieve_minhash(f"{video.id}-comment")
        transcript_mh = await recommenter.retrieve_minhash(f"{video.id}-transcript")
        if comment_mh is not None:
            minhashes[f"{video.id}-comment"] = comment_mh
            comment_lsh.insert(f"{video.id}-comment", comment_mh)
        if transcript_mh is not None:
            minhashes[f"{video.id}-transcript"] = transcript_mh
            transcript_lsh.insert(f"{video.id}-transcript", transcript_mh)
    async def get_related_videos(vid_id: str) -> Dict[str, Dict[str, float]]:
        results = {}  # type: Dict[str, Dict[str, float]]
        comment_mh_id = f"{vid_id}-comment"
        comment_mh = minhashes.get(comment_mh_id, None)
        transcript_mh_id = f"{vid_id}-transcript"
        transcript_mh = minhashes.get(transcript_mh_id, None)
        related_mh_ids = []  # type: List[str]
        if comment_mh is not None:
            related_mh_ids = related_mh_ids + comment_lsh.query(comment_mh)
        if transcript_mh is not None:
            related_mh_ids = related_mh_ids + transcript_lsh.query(transcript_mh)
        related_video_ids = list(set([mh_id.split('-')[0] for mh_id in related_mh_ids if mh_id != comment_mh_id and mh_id != transcript_mh_id]))
        for related_video_id in related_video_ids:
            related_comment_mh = minhashes.get(f"{related_video_id}-comment", None)
            related_transcript_mh = minhashes.get(f"{related_video_id}-transcript", None)
            if related_comment_mh is not None:
                if related_video_id not in results:
                    results[related_video_id] = {}
                results[related_video_id]['comment'] = comment_mh.jaccard(related_comment_mh)
            if related_transcript_mh is not None:
                if related_video_id not in results:
                    results[related_video_id] = {}
                results[related_video_id]['transcript'] = transcript_mh.jaccard(related_transcript_mh)
        return results
    print("Querying lsh")
    queried = {}
    for video in tqdm(videos):
        related = await get_related_videos(video.id)
        if related != {}:
            queried[video.id] = related
    #print(json.dumps(queried, indent=4))
    now = datetime.datetime.now()
    with open(f"{now.strftime('%Y-%m-%d-%H-%M-%S')}.json", "w+") as fp:
        fp.write(json.dumps(queried, indent=4))
    await recommenter.close()

async def reallyBruteSearch():
    recommenter = await Recommenter.create()  # type: Recommenter
    videos = recommenter.readFromSQL("videoInfo4.db")
    minhashes = {}
    print("Adding videos to lsh")
    for video in tqdm(videos):
        comment_mh = await recommenter.retrieve_minhash(f"{video.id}-comment")
        transcript_mh = await recommenter.retrieve_minhash(f"{video.id}-transcript-w3")
        if comment_mh is not None:
            minhashes[f"{video.id}-comment"] = comment_mh
        if transcript_mh is not None:
            minhashes[f"{video.id}-transcript-w3"] = transcript_mh
    async def get_related_videos(vid_id: str) -> Dict[str, Dict[str, float]]:
        results = {}  # type: Dict[str, Dict[str, float]]
        comment_mh_id = f"{vid_id}-comment"
        comment_mh = minhashes.get(comment_mh_id, None)
        transcript_mh_id = f"{vid_id}-transcript-w3"
        transcript_mh = minhashes.get(transcript_mh_id, None)
        if comment_mh is None or transcript_mh is None:
            return {}
        for related_video_id in [video.id for video in videos if video.id != vid_id]:
            related_comment_mh = minhashes.get(f"{related_video_id}-comment", None)
            related_transcript_mh = minhashes.get(f"{related_video_id}-transcript-w3", None)
            if related_comment_mh is not None and related_transcript_mh is not None:
                comment_score = comment_mh.jaccard(related_comment_mh)
                transcript_score = transcript_mh.jaccard(related_transcript_mh)
                if comment_score > 0.03 and transcript_score > 0.03:
                    results[related_video_id] = {}
                    results[related_video_id]['comment'] = comment_score
                    results[related_video_id]['transcript'] = transcript_score
        return results
    print("Querying lsh")
    queried = {}
    for video in tqdm(videos):
        related = await get_related_videos(video.id)
        if related != {}:
            queried[video.id] = related
    #print(json.dumps(queried, indent=4))
    now = datetime.datetime.now()
    with open(f"{now.strftime('%Y-%m-%d-%H-%M-%S')}.json", "w+") as fp:
        json.dump(queried, fp)
    with open(f"{now.strftime('%Y-%m-%d-%H-%M-%S')}.pretty.json", "w+") as fp:
        fp.write(json.dumps(queried, indent=4))
    await recommenter.close()

async def testHasKey():
    recommenter = await Recommenter.create()  # type: Recommenter
    ret = await recommenter.transcripts.has_key("Egp4NRhlMDg")
    print(ret)
    await recommenter.close()

# %%

# %%
loop = asyncio.new_event_loop()
# %%
# loop.run_until_complete(debugvid())
#loop.run_until_complete(testHasKey())
#loop.run_until_complete(populateDatabase())
# %%
# loop.run_until_complete(brutesearch())
loop.run_until_complete(reallyBruteSearch())