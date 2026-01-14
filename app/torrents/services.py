from . import models, utils
from app.core.database import redis_client
from.utils import redischeck
from app.core.proto.media_info_pb2 import MediaInfoSummary # type: ignore
from typing import List

def get_unique_key(unique_id: str):
    return f"mediafile:{unique_id}"

def get_imdb_key(imdb_id: str):
    return f"imdb:{imdb_id}"

def get_torrent_hash_key(hash_id: str, index: int = None):
    return f"thash:{hash_id}{':'+str(index) if index else ''}"

@redischeck()
def get_children_of_key(key: str):
    keys = []
    cursor = 0
    while True:
        cursor, batch = redis_client.scan(0, match=f"{key}*", count=10)
        keys.extend(batch)
        if cursor == 0:
            break
    return keys


@redischeck()
def get_unique_ids_from_torrent_hash(thash: str):
    thash_key = get_torrent_hash_key(thash)
    thash_keys = get_children_of_key(thash_key)
    return redis_client.mget(thash_keys)

@redischeck()
def get_media_from_uniqueid(unique_id: int):
    """
    Fetches a single media by uniqueid.
    """

    MediaInfoSummaryContext = MediaInfoSummary()

    unique_id_key = get_unique_key(unique_id)
    media_info = redis_client.get(unique_id_key)
    
    if media_info:
        return MediaInfoSummaryContext.ParseFromString(media_info)
    return None

@redischeck()
def get_medias_from_uniqueids(unique_ids: List[int]):
    """
    Fetches multiple medias by uniqueids.
    """

    MediaInfoSummaryContext = MediaInfoSummary()

    unique_id_keys = [get_unique_key(unique_id) for unique_id in unique_ids]

    media_infos = redis_client.mget(unique_id_keys)
    
    if len(media_infos) > 0:
        return {unique_id:MediaInfoSummaryContext.ParseFromString(media_info) for media_info,unique_id in zip(media_infos,unique_ids)}
    return None

@redischeck()
def get_media_from_imdb(imdb: str):
    """
    Fetches all media by imdb.
    """

    imdb_key = get_imdb_key(imdb)
    unique_id_key = redis_client.get(imdb_key)
    
    return get_media_from_uniqueid(unique_id_key)

@redischeck()
def get_media_from_torrent_hash(thash: str, index: int):
    """
    Fetches a single media by torrent hash and index.
    """ 

    thash_key = get_torrent_hash_key(thash, index)
    unique_id = redis_client.get(thash_key)
    
    return get_media_from_uniqueid(unique_id)

@redischeck()
def get_medias_from_torrent_hash(thash: str):
    """
    Fetches an entire torrent of media by torrent hash.
    """

    unique_ids = get_unique_ids_from_torrent_hash(thash)

    return get_medias_from_uniqueids(unique_ids)

@redischeck()
async def create_media_summary_from_mediainfo(json_media):
    """
    Creates a new media summary from mediainfo json in the Redis database.
    """

    summary_proto = utils.parse_mediainfo_json_to_proto(json_media)

    unique_id = summary_proto.unique_id
    imdb_id = summary_proto.imdb_id
    torrent_hash = summary_proto.torrent_hash
    torrent_file_index = summary_proto.torrent_file_index

    serialized_data = summary_proto.SerializeToString()

    unique_id_key = get_unique_key(unique_id)
    imdb_key = get_imdb_key(imdb_id)
    thash_key = get_torrent_hash_key(torrent_hash, torrent_file_index)

    #pipe = redis_client.pipeline()
    pipe = redis_client # Dont need a pipeline for now
    await pipe.set(unique_id_key, serialized_data)
    await pipe.set(thash_key, unique_id)
    await pipe.sadd(imdb_key, unique_id) # might not be able to do always
    #pipe.execute()

    response = models.MediaResponse(
        status="success",
        unique_id=unique_id,
        imdb_id=imdb_id,
        torrent_hash=torrent_hash,
        index=torrent_file_index
    )

    return response

# These two are the same thing just with different functions at the top
# Can they be combined?
# The top one doesn't really work correctly cause there is no imdb or torrent hash so when it adds to dragondb
# The key is just "" which will confuse later on
# so either clients need to add those and i need to update the models or it stores it without those
# I think people should be able to do both with the uniqueid serving as the real antiduplicate
# And i need to add antidupe checking


@redischeck()
async def create_media_summary_from_tracker(json_media):
    """
    Creates a new media summary from tracker json in the Redis database.
    """

    summary_proto = utils.parse_tracker_json_to_proto(json_media)

    print(summary_proto)

    unique_id = summary_proto.unique_id
    imdb_id = summary_proto.imdb_id
    torrent_hash = summary_proto.torrent_hash
    torrent_file_index = summary_proto.torrent_file_index

    serialized_data = summary_proto.SerializeToString()

    unique_id_key = get_unique_key(unique_id)
    imdb_key = get_imdb_key(imdb_id)
    thash_key = get_torrent_hash_key(torrent_hash, torrent_file_index)

    #pipe = redis_client.pipeline()
    pipe = redis_client # Dont need a pipeline for now
    await pipe.set(unique_id_key, serialized_data)
    await pipe.set(thash_key, unique_id)
    await pipe.sadd(imdb_key, unique_id) # might not be able to do always
    #pipe.execute()

    response = models.MediaResponse(
        status="success",
        unique_id=unique_id,
        imdb_id=imdb_id,
        torrent_hash=torrent_hash,
        index=torrent_file_index
    )

    return response

@redischeck()
def remove_media(unique_id_key: str, thash_key: str, imdb_key: str):
    redis_client.delete(unique_id_key, thash_key)
    redis_client.srem(imdb_key, unique_id_key[10:-1])

@redischeck()
def remove_medias(unique_id_keys: List[str], thash_keys: List[str], imdb_keys: List[str]):
    pipe = redis_client.pipeline()
    pipe.delete(*[unique_id_key for unique_id_key in unique_id_keys], *[thash_key for thash_key in thash_keys])
    for unique_id_key,imdb_key in zip(unique_id_keys,imdb_keys):
        pipe.srem(imdb_key, unique_id_key[10:0]) # Could optimize this whole thing to just do different srems for each imdb. But i can do that latter
    pipe.execute()

@redischeck()
def remove_media_from_uniqueid(unique_id: int):
    """
    Removes a media summary from the Redis database by uniqueid.
    """
    
    MediaSummary = get_media_from_uniqueid(unique_id)

    unique_id_key = get_unique_key(unique_id)
    thash_key = get_torrent_hash_key(MediaSummary["torrent_hash"], MediaSummary["torrent_file_index"])
    imdb_key = get_imdb_key(MediaSummary["imdb_id"])


    remove_media(unique_id_key, thash_key, imdb_key)

@redischeck()
def remove_media_from_torrent_hash(thash: str, index: int):
    """
    Removes a media summary from the Redis database by torrent hash and index.
    """
    
    MediaSummary = get_media_from_torrent_hash(thash, index)

    unique_id_key = get_unique_key(MediaSummary["unique_id"])
    thash_key = get_torrent_hash_key(thash, index)
    imdb_key = get_imdb_key(MediaSummary["imdb_id"])

    remove_media(unique_id_key, thash_key, imdb_key)

@redischeck()
def remove_medias_from_torrent_hash(thash: str):
    """
    Removes an entire torrent of media summaries from the Redis database by torrent hash.
    """
    
    thash_key = get_torrent_hash_key(thash)
    
    thash_keys = get_children_of_key(thash_key)

    unique_ids = redis_client.mget(*thash_keys)

    unique_id_keys = [get_unique_key(unique_id) for unique_id in unique_ids]

    MediaSummaries = get_medias_from_uniqueids(unique_ids)

    imdb_keys = [get_imdb_key(MediaSummary["imdb_id"]) for MediaSummary in MediaSummaries]

    remove_medias(unique_id_keys, thash_keys, imdb_keys)
    
    redis_client.delete(thash_key)