from typing import List, Optional, TypedDict
from pydantic import BaseModel, Field

class VideoSummary(BaseModel):
    """A compact summary of a single VIDEO track's key features."""
    codec: str = Field("", description='e.g., "HEVC", "AVC"')
    bit_depth: int = Field(0, description='e.g., 10, 8')
    width: int = Field(0, description='e.g., 3840')
    height: int = Field(0, description='e.g., 2160')
    hdr: str = Field("", description='e.g., "DV, HDR", "SDR"')
    is_3d: bool = Field(False, description='Is it a 3D video stream (e.g., H-SBS)?')
    has_hardcoded_subtitles: Optional[bool] = Field(None, description='Does this video track contain hardcoded subtitles?')
    source: Optional[str] = Field(None, description='e.g., "Warner Bros. USA UHD Blu-ray (2025)"')

class AudioSummary(BaseModel):
    """A compact summary of a single AUDIO track's key features."""
    language: Optional[str] = Field(None, description='e.g., "English", "Japanese"')
    format_tag: str = Field("", description='e.g., "Atmos", "TrueHD", "DTS-HD MA", "FLAC"')
    channels_tag: str = Field("", description='e.g., "7.1", "5.1", "2.0"')
    is_commentary: Optional[bool] = Field(None, description='Is this an audio commentary track?')
    is_descriptive: Optional[bool] = Field(None, description='Is this a descriptive audio track?')
    source: Optional[str] = Field(None, description='e.g., "Warner Bros. USA UHD Blu-ray (2025)"')

class SubtitleSummary(BaseModel):
    """A compact summary of a single SUBTITLE track's key features."""
    language: Optional[str] = Field(None, description='e.g., "English", "French"')
    format: Optional[str] = Field(None, description='e.g., "PGS", "SRT"')
    is_sdh: Optional[bool] = Field(None, description='Subtitles for the Deaf and Hard of Hearing?')
    source: Optional[str] = Field(None, description='e.g., "iTunes WEB-DL"')

class MediaInfoSummary(BaseModel):
    """The main "Hot" data object to be stored in Redis."""
    # --- Core Media Identifiers ---
    title: Optional[str] = Field(None, description='The title of the movie or episode.')
    imdb_id: Optional[str] = Field(None, description='e.g., "tt31193180"')
    tmdb_id: Optional[str] = Field(None, description='e.g., "movie/1233413"')
    unique_id: Optional[str] = Field(None, description='The 128-bit unique ID from the media container (e.g., MKV). Optional.')
    torrent_hash: str = Field("", description='The SHA256 hash of the torrent.')
    edition: Optional[str] = Field(None, description='e.g., "Director\'s Cut", "Extended Edition", "Uncut"')
    group: Optional[str] = Field(None, description='The release group, e.g., "CiNEPHiLES"')
    quality: Optional[str] = Field(None, description='e.g., "BluRay REMUX", "WEB-DL"')
    container: str = Field("", description='The file container, e.g., "mkv", "mp4"')
    size: int = Field(0, description='File size in bytes. Use int64 for large files.')
    site: Optional[str] = Field(None, description='The site the media originated from.')
    network: Optional[str] = Field(None, description='The TV network or streaming service.')

    # --- Boolean Flags ---
    extended: Optional[bool] = Field(None, description='Is this an extended version?')
    uncensored: Optional[bool] = Field(None, description='Is the content uncensored?')
    upscaled: Optional[bool] = Field(None, description='Is the video an upscale?')

    # --- TV Show Specific Fields (Hybrid Approach) ---
    season_number: Optional[int] = Field(None, description='The parsed season number, e.g., 1. Use 0 for specials.')
    episode_number: Optional[int] = Field(None, description='The parsed episode number, e.g., 1.')
    episode_string: Optional[str] = Field(None, description='The original display string, e.g., "S01E01", "S01E01-E02"')

    # --- Torrent Specific Field ---
    torrent_file_index: int = Field(0, description='The index of this file within the torrent (0, 1, 2...).')

    # --- Track Summaries (These are dynamic lists) ---
    # Use default_factory for mutable defaults like lists to avoid bugs
    video_tracks: List[VideoSummary] = Field(default_factory=list, description="A list of video track summaries")
    audio_tracks: List[AudioSummary] = Field(default_factory=list, description="A list of audio track summaries")
    subtitle_tracks: List[SubtitleSummary] = Field(default_factory=list, description="A list of subtitle track summaries")