import re
from app.core.proto.media_info_pb2 import MediaInfoSummary # type: ignore
from google.protobuf.json_format import MessageToDict
from app.core.database import redis_client
from .models import *
import uuid
from functools import wraps # W Wraps?
import os

def mediainfo_protobuf_to_dict(media_proto: MediaInfoSummary) -> MediaInfoSummaryModel:
    data_dict = MessageToDict(media_proto,
                  preserving_proto_field_name=True,
                  use_integers_for_enums=False
    )
    try:
        mediainfosummaryoutput = MediaInfoSummaryModel.model_validate(data_dict)
        return mediainfosummaryoutput
    except ValueError as e:
        print(f"Validation Error: {e}")
        return {"errors": True}

def parse_mediainfo_json_to_proto(source: MediaInfoFile) -> MediaInfoSummary:
    summary = MediaInfoSummary(
        mediainfo_version=source.creating_library.version
    )

    for track in source.media.tracks:
        
        # --- GENERAL TRACK ---
        if isinstance(track, GeneralTrack):
            summary.unique_id = track.unique_id
            summary.container = track.file_extension
            summary.size = track.file_size
            
            if track.title:
                summary.title = track.title
            elif source.media.ref:
                summary.title = os.path.splitext(os.path.basename(source.media.ref))[0]

        # --- VIDEO TRACK ---
        elif isinstance(track, VideoTrack):
            is_3d = False
            if track.multiview_count and track.multiview_count != "1":
                is_3d = True

            vid_sum = VideoSummary(
                codec=track.format,
                bit_depth=track.bit_depth,
                width=track.width,
                height=track.height,
                hdr=parse_hdr_features(track),
                is_3d=is_3d,
                source=track.source or track.title
            )
            summary.video_tracks.append(vid_sum)

        # --- AUDIO TRACK ---
        elif isinstance(track, AudioTrack):
            is_commentary = False
            is_descriptive = False
            
            combined_desc = f"{track.source or ''} {track.title or ''}".lower()
            
            if "commentary" in combined_desc:
                is_commentary = True
            if "descriptive" in combined_desc or "sdh" in combined_desc:
                is_descriptive = True

            aud_sum = AudioSummary(
                language=track.language,
                format_tag=track.format,
                channels_tag=parse_channel_layout(track.channel_layout, track.channels),
                is_commentary=is_commentary,
                is_descriptive=is_descriptive,
                source=track.source or track.title
            )
            summary.audio_tracks.append(aud_sum)

        # --- SUBTITLE TRACK ---
        elif isinstance(track, TextTrack):
            is_sdh = False
            combined_desc = f"{track.source or ''} {track.title or ''}".lower()
            
            if "sdh" in combined_desc or (track.language and "sdh" in track.language.lower()):
                is_sdh = True

            sub_sum = SubtitleSummary(
                language=track.language,
                format=track.format,
                is_sdh=is_sdh,
                source=track.source or track.title
            )
            summary.subtitle_tracks.append(sub_sum)


    return summary

def parse_channel_layout(layout: str, channel_count: int | str) -> str:
    """
    Calculates audio configuration from ChannelLayout string.
    Supports Standard (X.Y) and Object/Height (X.Y.Z) formats.
    
    Examples:
    'L R C LFE Ls Rs' -> "5.1"
    'L R C LFE Ls Rs Tfl Tfr' -> "5.1.2"
    """
    if not layout:
        try:
            c = int(channel_count)
            if c == 6: return "5.1"
            if c == 8: return "7.1"
            return f"{c}.0"
        except (ValueError, TypeError):
            return str(channel_count)

    speakers = layout.replace("  ", " ").strip().split(" ")
    
    lfe_count = 0
    height_count = 0
    bed_count = 0

    height_markers = ["TFL", "TFR", "TBL", "TBR", "TSL", "TSR", "TFC", "TBC", "VHL", "VHR", "TOP"]

    for s in speakers:
        s_upper = s.upper()
        
        if "LFE" in s_upper:
            lfe_count += 1
        elif any(s_upper.startswith(h) for h in height_markers) or "HEIGHT" in s_upper:
            height_count += 1
        else:
            bed_count += 1
    
    if height_count > 0:
        return f"{bed_count}.{lfe_count}.{height_count}"
    else:
        return f"{bed_count}.{lfe_count}"

def parse_hdr_features(track: VideoTrack) -> str:
    """
    Analyzes a VideoTrack to determine HDR capabilities.
    Checks Format, Compatibility, and Transfer Characteristics.
    """
    features = set()
    
    hdr_format = (track.hdr_format or "").strip()
    hdr_compat = (track.hdr_format_compatibility or "").strip()
    transfer = (track.transfer_characteristics or "").strip()
    
    full_string = f"{hdr_format} {hdr_compat}"

    # --- DOLBY VISION DETECTION ---
    is_dv = "Dolby Vision" in hdr_format
    if is_dv:
        features.add("DV")

    # --- HDR10+ DETECTION ---
    if "HDR10+" in full_string or "SMPTE ST 2094" in full_string:
        features.add("HDR10+")

    # --- HDR10 DETECTION ---
    # Check 1
    if "HDR10" in hdr_compat or "SMPTE ST 2086" in hdr_format:
        features.add("HDR10")
    
    # Check 2
    elif is_dv:
        if "HDR10" in full_string or "Blu-ray" in full_string:
            features.add("HDR10")
        else:
            profile_match = re.search(r'(?:Profile\s?|dvhe\.)0?([78])', full_string)
            if profile_match:
                features.add("HDR10")

    # Check 3
    if "HDR10" not in features and ("PQ" in transfer or "SMPTE ST 2084" in transfer):
        if not re.search(r'(?:Profile\s?|dvhe\.)0?5', full_string):
            features.add("HDR10")

    if "HLG" in transfer or "ARIB STD-B67" in transfer:
        features.add("HLG")

    if not features:
        return "SDR"

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

    # Populate Video Tracks
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

    # Populate Audio Tracks
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
            track_proto.format_tag = "DD" # Need to add DD+ and should this use Format or Codec ID? ALWAYS USE FORMAT FIX THIS BLUD
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

    for track_dict in mediainfo.get("Text", []):
        track_proto = summary.subtitle_tracks.add()
        track_proto.language = track_dict.get("Language", "")
        track_proto.source = track_dict.get("Source", "")
        
        format_str = track_dict.get("Format", "")

        if format_str == "PGS":
            track_proto.format = "PGS"
        elif format_str == "ASS":
            track_proto.format = "ASS"
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