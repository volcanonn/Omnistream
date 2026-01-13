from typing import List, Optional, Union, Literal
from pydantic import BaseModel, Field, ConfigDict

# -------------------------------------------------------------------------
# 1. General Track
# -------------------------------------------------------------------------
class GeneralTrack(BaseModel):
    """
    Represents the container information.
    Everything here is physically computed/present in valid media files.
    """
    model_config = ConfigDict(populate_by_name=True)

    track_type: Literal["General"] = Field(alias="@type")

    # --- Mandatory Computed Fields ---
    format: str = Field(alias="Format", description="e.g. Matroska, MPEG-4")
    format_version: Optional[str] = Field(None, alias="Format_Version", description="e.g. 4")
    file_extension: str = Field(alias="FileExtension", description="e.g. mkv, mp4")
    file_size: int = Field(alias="FileSize")
    duration: float = Field(alias="Duration", description="Duration in seconds")
    
    # "OverallBitRate" is always computed for the file container, even if specific tracks are VBR.
    overall_bit_rate: int = Field(alias="OverallBitRate")
    frame_rate: float = Field(alias="FrameRate", description="Container frame rate")
    
    video_count: Optional[Union[int, str]] = Field(0, alias="VideoCount")
    audio_count: Optional[Union[int, str]] = Field(0, alias="AudioCount")
    text_count: Optional[Union[int, str]] = Field(0, alias="TextCount")
    
    is_streamable: str = Field(alias="IsStreamable")

    # --- Optional Metadata ---
    unique_id: Optional[str] = Field(None, alias="UniqueID")
    title: Optional[str] = Field(None, alias="Title")
    movie: Optional[str] = Field(None, alias="Movie")
    encoded_application: Optional[str] = Field(None, alias="Encoded_Application")
    encoded_library: Optional[str] = Field(None, alias="Encoded_Library")

# -------------------------------------------------------------------------
# 2. Video Track
# -------------------------------------------------------------------------
class VideoTrack(BaseModel):
    """
    Represents a video stream.
    All physical dimensions and counts are Required.
    """
    model_config = ConfigDict(populate_by_name=True)

    track_type: Literal["Video"] = Field(alias="@type")
    
    # --- Mandatory Identification ---
    stream_order: Union[int, str] = Field(alias="StreamOrder")
    id: Union[int, str] = Field(alias="ID")
    unique_id: Optional[str] = Field(None, alias="UniqueID") # Optional (missing in MP4)

    # --- Mandatory Format/Codec ---
    format: str = Field(alias="Format", description="e.g. HEVC, AVC")
    codec_id: str = Field(alias="CodecID", description="e.g. V_MPEG4/ISO/AVC")
    
    # --- Mandatory Dimensions & properties ---
    width: int = Field(alias="Width")
    height: int = Field(alias="Height")
    sampled_width: int = Field(alias="Sampled_Width")
    sampled_height: int = Field(alias="Sampled_Height")
    pixel_aspect_ratio: float = Field(alias="PixelAspectRatio")
    display_aspect_ratio: float = Field(alias="DisplayAspectRatio")
    
    # --- Mandatory Timing & Counts ---
    duration: float = Field(alias="Duration")
    frame_rate: float = Field(alias="FrameRate")
    frame_rate_mode: str = Field(alias="FrameRate_Mode", description="CFR or VFR")
    frame_count: int = Field(alias="FrameCount")
    
    # --- Mandatory Color/Depth ---
    color_space: str = Field(alias="ColorSpace", description="e.g. YUV")
    chroma_subsampling: str = Field(alias="ChromaSubsampling", description="e.g. 4:2:0")
    bit_depth: int = Field(alias="BitDepth")
    scan_type: Optional[str] = Field(None, alias="ScanType", description="Progressive/Interlaced")
    
    # --- Mandatory Buffer/Delay ---
    delay: float = Field(alias="Delay")

    # --- Optional (Not always present in VBR/Remux) ---
    bit_rate: Optional[int] = Field(None, alias="BitRate")
    bit_rate_mode: Optional[str] = Field(None, alias="BitRate_Mode")
    stream_size: Optional[int] = Field(None, alias="StreamSize") # Missing in some HEVC Remuxes

    # --- Optional Metadata ---
    format_profile: Optional[str] = Field(None, alias="Format_Profile")
    title: Optional[str] = Field(None, alias="Title")
    language: Optional[str] = Field(None, alias="Language")
    default: Optional[str] = Field(None, alias="Default")
    forced: Optional[str] = Field(None, alias="Forced")
    
    # HDR (Optional)
    hdr_format: Optional[str] = Field(None, alias="HDR_Format")
    hdr_format_compatibility: Optional[str] = Field(None, alias="HDR_Format_Compatibility")
    
    # 3D (Optional)
    multiview_count: Optional[str] = Field(None, alias="MultiView_Count")

# -------------------------------------------------------------------------
# 3. Audio Track
# -------------------------------------------------------------------------
class AudioTrack(BaseModel):
    """
    Represents an audio stream.
    Physical layout and sampling are Required.
    """
    model_config = ConfigDict(populate_by_name=True)

    track_type: Literal["Audio"] = Field(alias="@type")

    # --- Mandatory Identification ---
    stream_order: Union[int, str] = Field(alias="StreamOrder")
    id: Union[int, str] = Field(alias="ID")
    unique_id: Optional[str] = Field(None, alias="UniqueID")

    # --- Mandatory Format ---
    format: str = Field(alias="Format")
    codec_id: str = Field(alias="CodecID")
    compression_mode: str = Field(alias="Compression_Mode", description="Lossy or Lossless")

    # --- Mandatory Specs ---
    duration: float = Field(alias="Duration")
    channels: Union[int, str] = Field(alias="Channels", description="int or string '8 / 6'")
    channel_positions: str = Field(alias="ChannelPositions")
    channel_layout: Optional[str] = Field(None, alias="ChannelLayout") # Usually present, but Positions is safer
    sampling_rate: int = Field(alias="SamplingRate")
    sampling_count: Optional[int] = Field(None, alias="SamplingCount")
    
    delay: Optional[float] = Field(0.0, alias="Delay")

    # --- Optional (Not always present in VBR/TrueHD) ---
    bit_rate: Optional[int] = Field(None, alias="BitRate")
    stream_size: Optional[int] = Field(None, alias="StreamSize")

    # --- Optional Metadata ---
    format_commercial: Optional[str] = Field(None, alias="Format_Commercial_IfAny")
    format_additional: Optional[str] = Field(None, alias="Format_AdditionalFeatures")
    title: Optional[str] = Field(None, alias="Title")
    language: Optional[str] = Field(None, alias="Language")
    default: Optional[str] = Field(None, alias="Default")
    forced: Optional[str] = Field(None, alias="Forced")

# -------------------------------------------------------------------------
# 4. Text Track
# -------------------------------------------------------------------------
class TextTrack(BaseModel):
    """
    Represents a subtitle stream.
    """
    model_config = ConfigDict(populate_by_name=True)

    track_type: Literal["Text"] = Field(alias="@type")

    # --- Mandatory Identification ---
    stream_order: Union[int, str] = Field(alias="StreamOrder")
    id: Union[int, str] = Field(alias="ID")

    # --- Mandatory Format ---
    format: str = Field(alias="Format")
    codec_id: str = Field(alias="CodecID")

    # --- Optional ---
    # Duration/FrameCount/BitRate often missing for empty or sparse subtitle tracks
    unique_id: Optional[str] = Field(None, alias="UniqueID")
    title: Optional[str] = Field(None, alias="Title")
    language: Optional[str] = Field(None, alias="Language")
    default: Optional[str] = Field(None, alias="Default")
    forced: Optional[str] = Field(None, alias="Forced")

# -------------------------------------------------------------------------
# 5. Image Track (Covers)
# -------------------------------------------------------------------------
class ImageTrack(BaseModel):
    """
    Represents embedded images (covers).
    """
    model_config = ConfigDict(populate_by_name=True)
    track_type: Literal["Image"] = Field(alias="@type")
    
    format: str = Field(alias="Format")
    width: int = Field(alias="Width")
    height: int = Field(alias="Height")
    color_space: str = Field(alias="ColorSpace")
    chroma_subsampling: str = Field(alias="ChromaSubsampling")
    compression_mode: str = Field(alias="Compression_Mode")

# -------------------------------------------------------------------------
# 6. Menu / Other
# -------------------------------------------------------------------------
class MenuTrack(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    track_type: Literal["Menu"] = Field(alias="@type")
    # Menu usually contains dynamic keys for chapters, so we leave it open or use extra

class OtherTrack(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    track_type: str = Field(alias="@type")

# -------------------------------------------------------------------------
# Root Objects
# -------------------------------------------------------------------------
class MediaObjectRaw(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    
    ref: Optional[str] = Field(None, alias="@ref")
    tracks: List[Union[GeneralTrack, VideoTrack, AudioTrack, TextTrack, ImageTrack, MenuTrack, OtherTrack]] = Field(alias="track")

class MediaInfoFile(BaseModel):
    """Root model for parsing."""
    media: MediaObjectRaw