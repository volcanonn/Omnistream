from typing import List, Optional, Union, Literal
from pydantic import BaseModel, Field, ConfigDict

class CreatingLibrary(BaseModel):
    """
    Metadata about the MediaInfo library version used to generate the JSON.
    """
    name: str = Field(description="e.g. MediaInfoLib")
    version: str = Field(description="e.g. 25.07")
    url: str = Field(description="e.g. https://mediaarea.net/MediaInfo")

class GeneralTrackExport(BaseModel):
    """
    Represents the container information.
    """
    model_config = ConfigDict(populate_by_name=True)

    track_type: Literal["General"] = Field(alias="@type")

    # --- Mandatory Computed Fields ---
    format: str = Field(alias="Format", description="e.g. Matroska, MPEG-4")
    format_version: Optional[str] = Field(None, alias="Format_Version")
    file_extension: str = Field(alias="FileExtension")
    file_size: int = Field(alias="FileSize")
    duration: float = Field(alias="Duration")
    
    overall_bit_rate: int = Field(alias="OverallBitRate")
    frame_rate: float = Field(alias="FrameRate")
    
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

class VideoTrackExport(BaseModel):
    """
    Represents a video stream.
    """
    model_config = ConfigDict(populate_by_name=True)

    track_type: Literal["Video"] = Field(alias="@type")
    
    # Mandatory Identification
    stream_order: Union[int, str] = Field(alias="StreamOrder")
    id: Union[int, str] = Field(alias="ID")
    unique_id: Optional[str] = Field(None, alias="UniqueID")

    # Mandatory Format/Codec
    format: str = Field(alias="Format")
    codec_id: str = Field(alias="CodecID")
    
    # Mandatory Dimensions & properties
    width: int = Field(alias="Width")
    height: int = Field(alias="Height")
    sampled_width: int = Field(alias="Sampled_Width")
    sampled_height: int = Field(alias="Sampled_Height")
    pixel_aspect_ratio: float = Field(alias="PixelAspectRatio")
    display_aspect_ratio: float = Field(alias="DisplayAspectRatio")
    
    # Mandatory Timing & Counts
    duration: float = Field(alias="Duration")
    frame_rate: float = Field(alias="FrameRate")
    frame_rate_mode: str = Field(alias="FrameRate_Mode")
    frame_count: int = Field(alias="FrameCount")
    
    # Mandatory Color/Depth
    color_space: str = Field(alias="ColorSpace")
    chroma_subsampling: str = Field(alias="ChromaSubsampling")
    bit_depth: int = Field(alias="BitDepth")
    scan_type: Optional[str] = Field(None, alias="ScanType")
    
    # Mandatory Buffer/Delay
    delay: float = Field(alias="Delay")

    # Optional (Remux/VBR specific)
    bit_rate: Optional[int] = Field(None, alias="BitRate")
    bit_rate_mode: Optional[str] = Field(None, alias="BitRate_Mode")
    stream_size: Optional[int] = Field(None, alias="StreamSize")

    # Optional Metadata
    format_profile: Optional[str] = Field(None, alias="Format_Profile")
    title: Optional[str] = Field(None, alias="Title")
    language: Optional[str] = Field(None, alias="Language")
    default: Optional[str] = Field(None, alias="Default")
    forced: Optional[str] = Field(None, alias="Forced")
    
    # HDR (Optional)
    hdr_format: Optional[str] = Field(None, alias="HDR_Format")
    hdr_format_compatibility: Optional[str] = Field(None, alias="HDR_Format_Compatibility")
    transfer_characteristics: Optional[str] = Field(None, alias="transfer_characteristics")
    
    # 3D (Optional)
    multiview_count: Optional[str] = Field(None, alias="MultiView_Count")

class AudioTrackExport(BaseModel):
    """
    Represents an audio stream.
    """
    model_config = ConfigDict(populate_by_name=True)

    track_type: Literal["Audio"] = Field(alias="@type")

    # Mandatory Identification
    stream_order: Union[int, str] = Field(alias="StreamOrder")
    id: Union[int, str] = Field(alias="ID")
    unique_id: Optional[str] = Field(None, alias="UniqueID")

    # Mandatory Format
    format: str = Field(alias="Format")
    codec_id: str = Field(alias="CodecID")
    compression_mode: str = Field(alias="Compression_Mode")

    # Mandatory Specs
    duration: float = Field(alias="Duration")
    channels: Union[int, str] = Field(alias="Channels")
    channel_positions: str = Field(alias="ChannelPositions")
    channel_layout: Optional[str] = Field(None, alias="ChannelLayout")
    sampling_rate: int = Field(alias="SamplingRate")
    sampling_count: Optional[int] = Field(None, alias="SamplingCount")
    
    delay: Optional[float] = Field(0.0, alias="Delay")

    # Optional
    bit_rate: Optional[int] = Field(None, alias="BitRate")
    stream_size: Optional[int] = Field(None, alias="StreamSize")
    format_commercial: Optional[str] = Field(None, alias="Format_Commercial_IfAny")
    format_additional: Optional[str] = Field(None, alias="Format_AdditionalFeatures")
    title: Optional[str] = Field(None, alias="Title")
    language: Optional[str] = Field(None, alias="Language")
    default: Optional[str] = Field(None, alias="Default")
    forced: Optional[str] = Field(None, alias="Forced")

class TextTrackExport(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    track_type: Literal["Text"] = Field(alias="@type")

    stream_order: Union[int, str] = Field(alias="StreamOrder")
    id: Union[int, str] = Field(alias="ID")

    format: str = Field(alias="Format")
    codec_id: str = Field(alias="CodecID")

    unique_id: Optional[str] = Field(None, alias="UniqueID")
    title: Optional[str] = Field(None, alias="Title")
    language: Optional[str] = Field(None, alias="Language")
    default: Optional[str] = Field(None, alias="Default")
    forced: Optional[str] = Field(None, alias="Forced")

class ImageTrackExport(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    track_type: Literal["Image"] = Field(alias="@type")
    
    format: str = Field(alias="Format")
    width: int = Field(alias="Width")
    height: int = Field(alias="Height")
    color_space: str = Field(alias="ColorSpace")
    chroma_subsampling: str = Field(alias="ChromaSubsampling")
    compression_mode: str = Field(alias="Compression_Mode")

class MenuTrackExport(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    track_type: Literal["Menu"] = Field(alias="@type")

class OtherTrackExport(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    track_type: str = Field(alias="@type")

class MediaObjectRaw(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    
    ref: Optional[str] = Field(None, alias="@ref")
    tracks: List[Union[GeneralTrackExport, VideoTrackExport, AudioTrackExport, TextTrackExport, ImageTrackExport, MenuTrackExport, OtherTrackExport]] = Field(alias="track")

class MediaInfoExport(BaseModel):
    """Root model for mediainfo.txt JSON parsing."""
    model_config = ConfigDict(populate_by_name=True)
    
    # Added CreatingLibrary here
    creating_library: CreatingLibrary = Field(alias="creatingLibrary")
    media: MediaObjectRaw