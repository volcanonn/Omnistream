from . import models, utils
from app.core.database import redis_client
from.utils import redischeck
from app.core.proto.media_info_pb2 import OmnistreamProtoSummary # type: ignore
from typing import List

def get_unique_key(unique_id):
    if type(unique_id) == bytes:
        unique_id = unique_id.decode('utf-8')
    return f"mediafile:{unique_id}"

def get_imdb_key(imdb_id: str):
    return f"imdb:{imdb_id}"

def get_torrent_hash_key(hash_id: str): #, index: int = None
    return f"thash:{hash_id}" #{':'+str(index) if index else ''}

@redischeck()
async def get_children_of_key(key: str): # NEVER USE THIS SHIT FUNCTION AGAIN IM RETARDED
    """
    DONT USE TS.
    """
    keys = []
    cursor = 0
    while True:
        cursor, batch = await redis_client.scan(0, match=f"{key}*", count=10)
        keys.extend(batch)
        if cursor == 0:
            break
    return keys

@redischeck()
async def get_unique_ids_from_torrent_hash(thash: str):
    thash_key = get_torrent_hash_key(thash)
    thash_map = await redis_client.hgetall(thash_key)
    return list(thash_map.values())

@redischeck()
async def get_media_from_uniqueid(unique_id):
    """
    Fetches a single media by uniqueid.
    """

    unique_id_key = get_unique_key(unique_id)
    media_info = await redis_client.get(unique_id_key)
    
    if media_info:
        OmnistreamProtoSummaryContext = OmnistreamProtoSummary()
        OmnistreamProtoSummaryContext.ParseFromString(media_info)
        return utils.omnistream_proto_summary_to_dict(OmnistreamProtoSummaryContext)
    return None

@redischeck()
async def get_medias_from_uniqueids(unique_ids: List):
    """
    Fetches multiple medias by uniqueids.
    """

    unique_id_keys = [get_unique_key(unique_id) for unique_id in unique_ids]

    media_infos = await redis_client.mget(unique_id_keys)
    
    if len(media_infos) > 0:
        output = []
        OmnistreamProtoSummaryContext = OmnistreamProtoSummary()
        for media_info in media_infos:
            OmnistreamProtoSummaryContext.Clear()
            OmnistreamProtoSummaryContext.ParseFromString(media_info)
            output.append(utils.omnistream_proto_summary_to_dict(OmnistreamProtoSummaryContext))
        """output = {}
        MediaInfoSummaryContext = MediaInfoSummary()
        for media_info,unique_id in zip(media_infos,unique_ids):
            MediaInfoSummaryContext.Clear()
            MediaInfoSummaryContext.ParseFromString(media_info)
            output.update({unique_id:utils.mediainfo_protobuf_to_dict(MediaInfoSummaryContext)})"""
        return output
    return None

@redischeck()
async def get_media_from_torrent_index(thash: str, index: str):
    """
    Fetches a single media by torrent hash and index.
    """ 

    thash_key = get_torrent_hash_key(thash)
    unique_id = await redis_client.hget(thash_key, index)
    
    return await get_media_from_uniqueid(unique_id)

# Need to add checks to all the redis_client gets
# Also i think all torrent indexes have to be strings cause they do
# Yea next thing is to do error handling for everything and returning errors instead of just 500
# make everything use format and not codec id also fix all the old funcs in utils
# I need to go through every thing and see if its supposed to be mediainfo text or mediainfo json or tracker and add models and do this all correctly cause now its really fucked up for everything
# add debug logger at some point

@redischeck()
async def get_medias_from_torrent_hash(thash: str):
    """
    Fetches an entire torrent of media by torrent hash.
    """

    unique_ids = await get_unique_ids_from_torrent_hash(thash)
    return await get_medias_from_uniqueids(unique_ids)

@redischeck()
async def get_medias_from_imdb(imdb: str):
    """
    Fetches all media by imdb.
    """

    imdb_key = get_imdb_key(imdb)
    unique_ids = await redis_client.smembers(imdb_key)

    if not unique_ids:
        return []
    
    return await get_medias_from_uniqueids(unique_ids)

async def process_lookup(params: models.MediaRequestParams) -> models.MediaDataResponse:
    if params.unique_id:
        result = [await get_media_from_uniqueid(params.unique_id)]
        
    elif params.imdb_id:
        result = await get_medias_from_imdb(params.imdb_id)
    
    elif params.index:
        result = [await get_media_from_torrent_index(params.torrent_hash, params.index)]

    elif params.torrent_hash:
        result = await get_medias_from_torrent_hash(params.torrent_hash)

    return models.MediaDataResponse(
        status="success",
        data=result
    )

@redischeck()
async def create_media_summary_from_mediainfo(json_media):
    """
    Creates a new media summary from mediainfo json in the Redis database.
    """

    summary_proto = utils.parse_mediainfo_export_to_proto(json_media)

    unique_id = summary_proto.unique_id
    imdb_id = summary_proto.imdb_id
    torrent_hash = summary_proto.torrent_hash
    torrent_file_index = summary_proto.torrent_file_index

    serialized_data = summary_proto.SerializeToString()

    unique_id_key = get_unique_key(unique_id)
    imdb_key = get_imdb_key(imdb_id)
    thash_key = get_torrent_hash_key(torrent_hash)

    #pipe = redis_client.pipeline()
    pipe = redis_client # Dont need a pipeline for now
    await pipe.set(unique_id_key, serialized_data)
    await pipe.hset(thash_key, str(torrent_file_index), unique_id)#await pipe.set(thash_key, unique_id)
    await pipe.sadd(imdb_key, unique_id) # might not be able to do always
    #pipe.execute()

    response = models.CreateMediaResponse(
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

    try:
        summary_proto = utils.parse_tracker_json_to_proto(json_media)

        unique_id = summary_proto.unique_id
        imdb_id = summary_proto.imdb_id
        torrent_hash = summary_proto.torrent_hash
        torrent_file_index = summary_proto.torrent_file_index

        serialized_data = summary_proto.SerializeToString()

        unique_id_key = get_unique_key(unique_id)
        imdb_key = get_imdb_key(imdb_id)
        thash_key = get_torrent_hash_key(torrent_hash)

        #pipe = redis_client.pipeline()
        pipe = redis_client # Dont need a pipeline for now
        await pipe.set(unique_id_key, serialized_data)
        await pipe.hset(thash_key, str(torrent_file_index), unique_id)#await pipe.set(thash_key, unique_id)
        await pipe.sadd(imdb_key, unique_id) # might not be able to do always
        #pipe.execute()

        response = models.CreateMediaResponse(
            status="success",
            unique_id=unique_id,
            imdb_id=imdb_id,
            torrent_hash=torrent_hash,
            index=torrent_file_index
        )
    except Exception as e:
        print(e)
        response = models.CreateMediaResponse(
            status="failed",
            unique_id=unique_id,
            imdb_id=imdb_id,
            torrent_hash=torrent_hash,
            index=torrent_file_index
        )

    return response

@redischeck()
async def remove_media(unique_id: str, thash_key: str, index: int, imdb_key: str):
    pipe = await redis_client.pipeline()
    pipe.delete(get_unique_key(unique_id))
    pipe.hdel(thash_key, index)
    pipe.srem(imdb_key, unique_id)
    await pipe.execute()

@redischeck()
async def remove_media_by_uniqueid(unique_id: str):
    """
    Removes a media summary from the Redis database by uniqueid.
    """
    
    MediaSummary = await get_media_from_uniqueid(unique_id)

    thash_key = get_torrent_hash_key(MediaSummary["torrent_hash"])
    imdb_key = get_imdb_key(MediaSummary["imdb_id"])

    await remove_media(unique_id, thash_key, MediaSummary["torrent_file_index"], imdb_key)

@redischeck()
async def remove_media_from_torrent_index(thash: str, index: int):
    """
    Removes a media summary from the Redis database by torrent hash and index.
    """
    
    MediaSummary = await get_media_from_torrent_index(thash, index)

    thash_key = get_torrent_hash_key(thash)
    imdb_key = get_imdb_key(MediaSummary["imdb_id"])

    await remove_media(MediaSummary["unique_id"], thash_key, index, imdb_key)

@redischeck()
async def remove_medias_from_torrent_hash(thash: str):
    """
    Removes an entire torrent of media summaries from the Redis database by torrent hash.
    """

    unique_ids = await get_unique_ids_from_torrent_hash(thash)

    MediaSummaries = await get_medias_from_uniqueids(unique_ids)

    imdb_keys_uniqueid = {}

    # Batch unique ids by imdb
    for MediaSummary in MediaSummaries:
        if not imdb_keys_uniqueid.get(MediaSummary["imdb_id"]):
            imdb_keys_uniqueid.update({MediaSummary["imdb_id"]:[]})
        imdb_keys_uniqueid[MediaSummary["imdb_id"]].append(MediaSummary["unique_id"])

    # W speed up by batching srem calls by imdb instead of calling it for every unique id even if they had the same imdb

    pipe = await redis_client.pipeline()
    pipe.delete(*[get_unique_key(unique_id) for unique_id in unique_ids], get_torrent_hash_key(thash))
    for imdb_key,unique_ids in enumerate(imdb_keys_uniqueid):
        pipe.srem(get_imdb_key(imdb_key), *unique_ids)
    await pipe.execute()

@redischeck()
async def remove_medias_from_imdb(imdb: str):
    """
    Removes all media summaries for a imdb from the Redis database.
    """
    pass