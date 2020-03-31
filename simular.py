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

print('Taking these files as input:', str(sys.argv[1:]))

k = 1
sample_size = 400
print('Generating shingles k=', k)

filenames = []
index = []
for filename in sys.argv[1:]:
    with open(filename) as fp:
        contents = fp.read().replace('\n', ' ')
        shingles = w_shingle(contents, k)
        shingles = set(shingles)
        if (len(shingles)) < sample_size:
            continue  # don't save, not enough shingles
        index.append(shingles)
        filenames.append(filename)

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


from datasketch import MinHash, MinHashLSH

# Create LSH index
threshold = 0.3
lsh = MinHashLSH(threshold=threshold, num_perm=100)

for i in range(len(filenames)):
    m = MinHash(num_perm=100)
    for shingle in index[i]:
        m.update(shingle.encode('utf8'))
    lsh.insert(filenames[i], m)

result = lsh.query(m)
print("Approximate neighbours with Jaccard similarity >", threshold, "for", filenames[i], result)
