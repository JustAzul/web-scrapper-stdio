from dataclasses import dataclass


@dataclass
class AntiDetectionConfig:
    """Configuration for anti-detection measures."""

    # User-Agent rotation
    enable_user_agent_rotation: bool = True
    user_agent_rotation_frequency: int = 5  # Requests per rotation

    # Header randomization
    enable_header_randomization: bool = True
    randomize_accept_language: bool = True
    randomize_accept_encoding: bool = True
    randomize_connection_header: bool = True

    # Timing randomization
    enable_timing_randomization: bool = True
    min_delay_seconds: float = 1.0
    max_delay_seconds: float = 3.0
    human_like_delays: bool = True

    # Fingerprint reduction
    enable_fingerprint_reduction: bool = True
    disable_webgl: bool = True
    disable_canvas_fingerprinting: bool = True
    randomize_screen_resolution: bool = True

    # Advanced features
    enable_request_headers_variation: bool = True
    enable_connection_pooling: bool = False
    max_concurrent_requests: int = 3
