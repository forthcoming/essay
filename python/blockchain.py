import hashlib,json
from time import time

blockchain = []

def hash(height,data,timestamp,previous_hash):
    sha = hashlib.sha256()
    sha.update(f"{height}{data}{timestamp}{previous_hash}".encode("utf8"))
    return sha.hexdigest()

def make_a_block(height,data,timestamp,previous_hash):
    blockchain.append({
        "height":height,
        "data":data,
        "timestamp":timestamp,
        "previous_hash":previous_hash,
        "hash":hash(height,data,timestamp,previous_hash)
    })

def add_a_block(data):
    last_block=blockchain[-1]
    height=last_block['height']+1
    timestamp=int(time() * 1000)
    previous_hash=last_block["hash"]
    make_a_block(height,data,timestamp,previous_hash)

def make_a_genesis_block():
    timestamp=int(time() * 1000)
    make_a_block(0,'genesis block',timestamp,0)

if __name__ == '__main__':
    make_a_genesis_block()
    add_a_block("this is block 1")
    add_a_block("this is block 2")
    add_a_block("this is block 3")
    print(json.dumps(blockchain))
