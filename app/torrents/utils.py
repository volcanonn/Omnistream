import re
from app.core.proto.media_info_pb2 import MediaInfoSummary # type: ignore
from app.core.database import redis_client
from .models import *
import uuid
from functools import wraps # W Wraps?

def parse_mediainfo_json_to_proto(media_json: dict) -> MediaInfoSummary:
    summary = MediaInfoSummary()
    summary.mediainfo_version = media_json.creating_library.version
    for track in media_json.media.tracks:
        match track.track_type:
            case "General":
                summary.title = track.title
                summary.unique_id = track.unique_id or "jiggle"
    return summary

def parse_hdr_features(hdr_string: str) -> str:
    """
    Parses the complex HDR format string to extract a clean list of features.
    Handles Dolby Vision profile rules for HDR10 compatibility.
    """
    if not isinstance(hdr_string, str) or not hdr_string:
        return "SDR"

    features = set()

    # 1. Check for Dolby Vision
    is_dv = "Dolby Vision" in hdr_string
    if is_dv:
        features.add("DV")

    # 2. Check for HDR10+
    if "HDR10+" in hdr_string:
        features.add("HDR10+")

    # 3. Determine HDR10 compatibility
    is_hdr10_compatible = "HDR10 compatible" in hdr_string

    # The robust check: if it's DV, check the profile number.
    # Profiles 7 and 8 are HDR10 compatible. Profile 5 is not.
    if is_dv:
        profile_match = re.search(r'Profile (\d+)|dvhe\.(\d+)', hdr_string)
        if profile_match:
            # group(1) is for "Profile X", group(2) is for "dvhe.XX"
            profile_num_str = profile_match.group(1) or profile_match.group(2)
            profile_num = int(profile_num_str)
            
            # Profiles 7 and 8 have an HDR10 base layer.
            if profile_num in [7, 8]:
                is_hdr10_compatible = True
        # If we can't determine profile but the string says compatible, trust it.
        elif "Blu-ray compatible" in hdr_string:
             is_hdr10_compatible = True

    if is_hdr10_compatible:
        features.add("HDR10")
        
    # 4. Fallback for plain HDR10 (if not already found via DV compatibility)
    if "SMPTE ST 2086" in hdr_string and "HDR10" not in features:
        features.add("HDR10")

    if not features:
        return "SDR"

    # Sort for consistent ordering, e.g., "DV, HDR10, HDR10+"
    return ", ".join(sorted(list(features)))

def parse_tracker_json_to_proto(tracker_json: Unit3dTorrent) -> MediaInfoSummary:
    mediainfo_dict = parse_mediainfo_text_to_dict(tracker_json.attributes.media_info)
    if mediainfo_dict.get("errors"):
        return {"errors":True}
    #print(mediainfo_dict)
    tracker_proto = tracker_dict_to_proto(tracker_json, mediainfo_dict["General"]["Complete name"])
    mediainfo_proto = mediainfo_dict_to_proto(mediainfo_dict)
    finalproto = MediaInfoSummary()
    finalproto.MergeFrom(tracker_proto)
    finalproto.MergeFrom(mediainfo_proto)
    return finalproto


def parse_mediainfo_text_to_dict(media_text: str) -> dict:
    removewhitespace = re.compile(r'^[\\. ]+')
    splitdict = re.compile(r'(?:[\\. ]+:? |[\\. ]*: )')
    try:
        torrentinfo = {}
        for stream in re.split('\n ?\n',media_text.replace("\r", "")):
            text = stream.split("\n")
            id = text.pop(0)
            if id[:6] == "Report":
                torrentinfo.update({"Report":re.split(splitdict,id)[1]})
                continue
            ogid = id
            if id.find(" #"):
                id = id.split(" #")[0]
            if not torrentinfo.get(id):
                torrentinfo.update({id:[]})
            info = []
            ConformanceInfo = [False,0]
            for value in text:
                newvalue = re.split(removewhitespace,value,maxsplit=1).pop()
                dictparts = re.split(splitdict,newvalue,maxsplit=1)
                if '' in dictparts:
                    keypart = f"key: {dictparts[0]}"
                    if dictparts[0] == '':
                        keypart = ''
                    print(f"Dict is missing part! torrent:  id: {ogid}" + keypart)
                    continue
                if len(dictparts) != 2:
                    print(f"Dict doesn't have exactly key and value! torrent:  id: {ogid} key: {dictparts[0]}")
                    continue
                if dictparts[0] == "Conformance errors":
                    ConformanceInfo[0] = True
                    ConformanceInfo[1] = len(info)
                    dictparts = ['Errors', dict([dictparts])]
                    info.append(dictparts)
                    continue
                if ConformanceInfo[0] == True:
                    info[ConformanceInfo[1]][1].update(dict([dictparts]))
                    continue
                info.append(dictparts)
            if id == "General":
                torrentinfo.update({id:dict(info)})
                continue
            torrentinfo[id].append(dict(info))
        return torrentinfo
        #aitherscrapped[pagenum][torrentnum]["attributes"].update({'media_info_serialized':torrentinfo})
    except Exception as e:
        return {"errors":True}

def mediainfo_dict_to_proto(mediainfo: dict) -> MediaInfoSummary:
    summary = MediaInfoSummary()

    general = mediainfo.get("General", {})

    summary.container = general.get("Format", "").lower()
    
    unique_id_raw = general.get("Unique ID", "")

    match = re.search(r'\(0x([0-9A-F]+)\)', unique_id_raw)
    if match:
        summary.unique_id = match.group(1).lower()
    else:
        summary.unique_id = uuid.uuid4().hex # Need to change to sha or smth else cause this aint gonna work fam fo shizzle city boooyyyyyy

    # --- 2. Populate Video Tracks ---
    for track_dict in mediainfo.get("Video", []):
        track_proto = summary.video_tracks.add()
        track_proto.codec = track_dict.get("Format", "")

        bit_depth_str = str(track_dict.get("Bit depth", "0"))
        width_str = str(track_dict.get("Width", "0"))
        height_str = str(track_dict.get("Height", "0"))

        track_proto.bit_depth = int(re.sub(r'\D', '', bit_depth_str))
        track_proto.width = int(re.sub(r'\D', '', width_str))
        track_proto.height = int(re.sub(r'\D', '', height_str))

        track_proto.source = track_dict.get("Source", "")
        
        hdr_format_string = track_dict.get("HDR format", "")
        track_proto.hdr = parse_hdr_features(hdr_format_string)

    # --- 3. Populate Audio Tracks ---
    for track_dict in mediainfo.get("Audio", []):
        track_proto = summary.audio_tracks.add()
        track_proto.language = track_dict.get("Language", "")
        track_proto.source = track_dict.get("Source", "")

        commercial_name = track_dict.get("Commercial name", "")
        if "Atmos" in commercial_name:
            track_proto.format_tag = "Atmos"
        elif "TrueHD" in commercial_name:
            track_proto.format_tag = "TrueHD"
        elif "Dolby Digital" in commercial_name:
            track_proto.format_tag = "DD" # Need to add DD+ and should this use Format or Codec ID?
        else:
            track_proto.format_tag = track_dict.get("Format", "")

        channels_str = str(track_dict.get("Channel(s)", "0"))
        if re.findall(r'\d* channels',channels_str):
            channels = int(re.sub(r'\D', '', channels_str))

            if channels >= 8: track_proto.channels_tag = "7.1"
            elif channels >= 6: track_proto.channels_tag = "5.1"
            else: track_proto.channels_tag = "2.0"
        elif channels_str == "Object Based":
            track_proto.channels_tag = "Object Based"
        else:
            track_proto.channels_tag = ""
            

        title = track_dict.get("Title", "").lower()
        if "commentary" in title:
            track_proto.is_commentary = True
        if "descriptive" in title:
            track_proto.is_descriptive = True

    # --- 4. Populate Subtitle Tracks ---
    for track_dict in mediainfo.get("Text", []):
        track_proto = summary.subtitle_tracks.add()
        track_proto.language = track_dict.get("Language", "")
        track_proto.source = track_dict.get("Source", "")
        
        # Get the format string from the JSON
        format_str = track_dict.get("Format", "")

        # Use an if/elif/else block to handle multiple known formats
        if format_str == "PGS":
            track_proto.format = "PGS"
        elif format_str == "ASS":
            track_proto.format = "ASS"
        # We can also handle SSA, the predecessor to ASS
        elif format_str == "SSA":
            track_proto.format = "SSA"
        # All other text-based formats (like UTF-8) will be standardized as SRT
        else:
            track_proto.format = "SRT"
        
        title = track_dict.get("Title", "").lower()
        if "sdh" in title:
            track_proto.is_sdh = True

    return summary


def tracker_dict_to_proto(tracker_dict: Unit3dTorrent, filename = None) -> MediaInfoSummary:
    summary = MediaInfoSummary()

    data = tracker_dict.attributes

    summary.title = data.name # Get title before year
    summary.imdb_id = f"tt{str(data.imdb_id).zfill(7)}"
    summary.tmdb_id = str(data.tmdb_id)
    summary.size = data.size
    summary.torrent_hash = data.info_hash[-32:] # just makin up shi
    summary.quality = data.type
    
    if filename:
        for i,v in enumerate(data.files):
            if v.name == filename:
                summary.torrent_file_index = i
                #print(media_json.get("info_hash", "")[-32:],i)

    return summary

def redischeck():
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not redis_client:
                raise ConnectionError("Database connection is not available.")
            return func(*args, **kwargs)
        return wrapper
    return decorator