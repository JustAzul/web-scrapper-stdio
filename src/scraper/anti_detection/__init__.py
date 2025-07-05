"""
Anti-Detection Measures Implementation for Web Scraper MCP.

This module implements comprehensive anti-detection measures to avoid bot detection
following T027 requirements:

1. User-Agent rotation with realistic browser signatures
2. HTTP header randomization to appear human-like
3. Timing randomization to simulate human behavior
4. Browser fingerprint reduction techniques
5. Coordinated anti-detection management

TDD Implementation: GREEN phase - comprehensive anti-detection system.
"""

import asyncio
import random
import secrets
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from src.logger import get_logger

from .config import AntiDetectionConfig

logger = get_logger(__name__)

# Secure random generator instance for anti-detection
_secure_random = secrets.SystemRandom()

# Public API for the anti_detection module
__all__ = [
    "AntiDetectionManager",
    "AntiDetectionConfig",
    "UserAgentRotator",
    "HeaderRandomizer",
    "TimingRandomizer",
    "FingerprintReducer",
    "create_anti_detection_manager",
    "create_stealth_config",
    "create_balanced_config",
    "create_performance_config",
]


class BrowserType(Enum):
    """Browser types for user-agent rotation."""

    CHROME = "chrome"
    FIREFOX = "firefox"
    SAFARI = "safari"
    EDGE = "edge"


class Platform(Enum):
    """Operating system platforms."""

    WINDOWS = "windows"
    MACOS = "macos"
    LINUX = "linux"


@dataclass
class UserAgentProfile:
    """User agent profile with browser and platform information."""

    user_agent: str
    browser_type: BrowserType
    platform: Platform
    version: str
    market_share: float  # For weighted selection
    headers: Dict[str, str] = field(default_factory=dict)


class UserAgentRotator:
    """Manages user-agent rotation with realistic browser signatures."""

    def __init__(self, config: AntiDetectionConfig):
        self.config = config
        self.logger = get_logger(__name__)
        self.current_profile: Optional[UserAgentProfile] = None
        self.request_count = 0
        self.profiles = self._load_user_agent_profiles()

    def _load_user_agent_profiles(self) -> List[UserAgentProfile]:
        """Load realistic user-agent profiles with current browser versions."""
        self.profiles.extend(
            [
                # Chrome profiles
                UserAgentProfile(
                    user_agent=(
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/120.0.0.0 Safari/537.36"
                    ),
                    browser_type=BrowserType.CHROME,
                    platform=Platform.WINDOWS,
                    headers={
                        "accept": (
                            "text/html,application/xhtml+xml,application/xml;q=0.9,"
                            "image/avif,image/webp,image/apng,*/*;q=0.8,"
                            "application/signed-exchange;v=b3;q=0.7"
                        ),
                        "accept-language": "en-US,en;q=0.9",
                        "sec-ch-ua": (
                            '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"'
                        ),
                        "sec-ch-ua-mobile": "?0",
                        "sec-ch-ua-platform": '"Windows"',
                        "sec-fetch-dest": "document",
                        "sec-fetch-mode": "navigate",
                        "sec-fetch-site": "none",
                        "sec-fetch-user": "?1",
                        "upgrade-insecure-requests": "1",
                    },
                ),
                UserAgentProfile(
                    user_agent=(
                        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/120.0.0.0 Safari/537.36"
                    ),
                    browser_type=BrowserType.CHROME,
                    platform=Platform.MACOS,
                    headers={
                        "accept": (
                            "text/html,application/xhtml+xml,application/xml;q=0.9,"
                            "image/avif,image/webp,image/apng,*/*;q=0.8,"
                            "application/signed-exchange;v=b3;q=0.7"
                        ),
                        "accept-language": "en-US,en;q=0.9",
                        "sec-ch-ua": (
                            '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"'
                        ),
                        "sec-ch-ua-mobile": "?0",
                        "sec-ch-ua-platform": '"macOS"',
                        "sec-fetch-dest": "document",
                        "sec-fetch-mode": "navigate",
                        "sec-fetch-site": "none",
                        "sec-fetch-user": "?1",
                        "upgrade-insecure-requests": "1",
                    },
                ),
                UserAgentProfile(
                    user_agent=(
                        "Mozilla/5.0 (X11; Linux x86_64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/120.0.0.0 Safari/537.36"
                    ),
                    browser_type=BrowserType.CHROME,
                    platform=Platform.LINUX,
                ),
                # Firefox profiles
                UserAgentProfile(
                    user_agent=(
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) "
                        "Gecko/20100101 Firefox/121.0"
                    ),
                    browser_type=BrowserType.FIREFOX,
                    platform=Platform.WINDOWS,
                ),
                UserAgentProfile(
                    user_agent=(
                        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) "
                        "Gecko/20100101 Firefox/121.0"
                    ),
                    browser_type=BrowserType.FIREFOX,
                    platform=Platform.MACOS,
                ),
                # Safari profiles
                UserAgentProfile(
                    user_agent=(
                        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                        "AppleWebKit/605.1.15 (KHTML, like Gecko) "
                        "Version/17.2 Safari/605.1.15"
                    ),
                    browser_type=BrowserType.SAFARI,
                    platform=Platform.MACOS,
                ),
                # Edge profiles
                UserAgentProfile(
                    user_agent=(
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0"
                    ),
                    browser_type=BrowserType.EDGE,
                    platform=Platform.WINDOWS,
                ),
            ]
        )

        self.logger.debug(f"Loaded {len(self.profiles)} user-agent profiles")
        return self.profiles

    def get_user_agent(self, force_rotation: bool = False) -> str:
        """
        Get current user-agent, rotating if necessary.

        Args:
            force_rotation: Force rotation regardless of frequency

        Returns:
            User-agent string
        """
        if not self.config.enable_user_agent_rotation:
            return self.profiles[0].user_agent  # Default to first profile

        # Check if rotation is needed
        should_rotate = (
            force_rotation
            or self.current_profile is None
            or self.request_count >= self.config.user_agent_rotation_frequency
        )

        if should_rotate:
            self.current_profile = self._select_weighted_profile()
            self.request_count = 0
            self.logger.debug(
                f"Rotated to user-agent: {self.current_profile.browser_type.value}"
            )

        self.request_count += 1
        return self.current_profile.user_agent

    def _select_weighted_profile(self) -> UserAgentProfile:
        """Select user-agent profile based on market share weights."""
        total_weight = sum(profile.market_share for profile in self.profiles)
        # Use secrets for cryptographically secure randomness
        random_value = secrets.SystemRandom().uniform(0, total_weight)

        cumulative_weight = 0
        for profile in self.profiles:
            cumulative_weight += profile.market_share
            if random_value <= cumulative_weight:
                return profile

        # Fallback to first profile
        return self.profiles[0]

    def get_current_profile(self) -> Optional[UserAgentProfile]:
        """Get current user-agent profile."""
        return self.current_profile


class HeaderRandomizer:
    """Randomizes HTTP headers to appear more human-like."""

    def __init__(self, config: AntiDetectionConfig):
        self.config = config
        self.logger = get_logger(__name__)

    def get_randomized_headers(
        self, base_headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, str]:
        """
        Generate randomized HTTP headers.

        Args:
            base_headers: Base headers to extend

        Returns:
            Dictionary of randomized headers
        """
        headers = base_headers.copy() if base_headers else {}

        if not self.config.enable_header_randomization:
            return headers

        # Randomize Accept-Language
        if self.config.randomize_accept_language:
            headers["Accept-Language"] = self._get_random_accept_language()

        # Randomize Accept-Encoding
        if self.config.randomize_accept_encoding:
            headers["Accept-Encoding"] = self._get_random_accept_encoding()

        # Randomize Connection header
        if self.config.randomize_connection_header:
            headers["Connection"] = _secure_random.choice(["keep-alive", "close"])

        # Add common browser headers with variation
        if self.config.enable_request_headers_variation:
            headers.update(self._get_varied_browser_headers())

        self.logger.debug(f"Generated {len(headers)} randomized headers")
        return headers

    def _get_random_accept_language(self) -> str:
        """Generate random Accept-Language header."""
        languages = [
            "en-US,en;q=0.9",
            "en-US,en;q=0.9,es;q=0.8",
            "en-GB,en;q=0.9",
            "en-US,en;q=0.9,fr;q=0.8",
            "en-US,en;q=0.9,de;q=0.8",
            "en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7",
        ]
        return _secure_random.choice(languages)

    def _get_random_accept_encoding(self) -> str:
        """Generate random Accept-Encoding header."""
        encodings = [
            "gzip, deflate, br",
            "gzip, deflate",
            "gzip, deflate, br, zstd",
        ]
        return _secure_random.choice(encodings)

    def _get_varied_browser_headers(self) -> Dict[str, str]:
        """Generate varied browser-specific headers."""
        headers = {}

        # Vary DNT (Do Not Track) header
        if _secure_random.random() < 0.3:  # 30% chance
            headers["DNT"] = "1"

        # Vary Upgrade-Insecure-Requests
        if _secure_random.random() < 0.8:  # 80% chance
            headers["Upgrade-Insecure-Requests"] = "1"

        # Vary Sec-Fetch headers (modern browsers)
        if _secure_random.random() < 0.9:  # 90% chance
            headers["Sec-Fetch-Dest"] = _secure_random.choice(["document", "empty"])
            headers["Sec-Fetch-Mode"] = _secure_random.choice(["navigate", "cors"])
            headers["Sec-Fetch-Site"] = _secure_random.choice(
                ["none", "same-origin", "cross-site"]
            )

        return headers


class TimingRandomizer:
    """Randomizes request timing to simulate human behavior."""

    def __init__(self, config: AntiDetectionConfig):
        self.config = config
        self.logger = get_logger(__name__)

    async def apply_delay(self, force_delay: bool = False) -> float:
        """
        Apply a random delay to simulate human-like behavior.

        Args:
            force_delay: Force delay even if disabled in config

        Returns:
            The applied delay in seconds
        """
        if not self.config.enable_timing_randomization and not force_delay:
            return 0.0

        if self.config.human_like_delays:
            delay = self._get_human_like_delay()
        else:
            delay = _secure_random.uniform(
                self.config.min_delay_seconds, self.config.max_delay_seconds
            )

        # In case of force_delay, ensure there is a minimal delay
        if force_delay and delay == 0.0:
            delay = _secure_random.uniform(0.5, 1.5)

        self.logger.debug(f"Applying delay of {delay:.2f} seconds")
        await asyncio.sleep(delay)
        return delay

    def _get_human_like_delay(self) -> float:
        """Generate human-like delay using normal distribution."""
        # Human reading/interaction patterns: most delays 1-3s, some longer
        mean_delay = (self.config.min_delay_seconds + self.config.max_delay_seconds) / 2
        std_dev = (self.config.max_delay_seconds - self.config.min_delay_seconds) / 4

        delay = _secure_random.normalvariate(mean_delay, std_dev)

        # Clamp to configured bounds
        delay = max(
            self.config.min_delay_seconds, min(delay, self.config.max_delay_seconds)
        )

        return delay


class FingerprintReducer:
    """Reduces browser fingerprinting detectability."""

    def __init__(self, config: AntiDetectionConfig):
        self.config = config
        self.logger = get_logger(__name__)

    def get_browser_args(self) -> List[str]:
        """
        Get browser launch arguments for fingerprint reduction.

        Returns:
            List of browser arguments
        """
        args = []

        if not self.config.enable_fingerprint_reduction:
            return args

        # Disable WebGL
        if self.config.disable_webgl:
            args.extend(
                [
                    "--disable-webgl",
                    "--disable-webgl2",
                    "--disable-3d-apis",
                ]
            )

        # Disable canvas fingerprinting
        if self.config.disable_canvas_fingerprinting:
            args.extend(
                [
                    "--disable-canvas-aa",
                    "--disable-2d-canvas-clip-aa",
                ]
            )

        # Additional fingerprint reduction
        args.extend(
            [
                "--disable-web-security",
                "--disable-features=VizDisplayCompositor",
                "--disable-backgrounding-occluded-windows",
                "--disable-renderer-backgrounding",
                "--disable-background-timer-throttling",
                "--disable-background-networking",
                "--disable-plugins-discovery",
                "--no-first-run",
                "--no-default-browser-check",
            ]
        )

        self.logger.debug(f"Generated {len(args)} fingerprint reduction arguments")
        return args

    def get_viewport_size(self) -> Tuple[int, int]:
        """
        Get randomized viewport size to reduce fingerprinting.

        Returns:
            Tuple of (width, height)
        """
        if not self.config.randomize_screen_resolution:
            return (1920, 1080)  # Default resolution

        # Common desktop resolutions with slight randomization
        base_resolutions = [
            (1920, 1080),
            (1366, 768),
            (1536, 864),
            (1440, 900),
            (1280, 720),
        ]

        width, height = _secure_random.choice(base_resolutions)

        # Add small random variation (±10 pixels)
        width += _secure_random.randint(-10, 10)
        height += _secure_random.randint(-10, 10)

        return (width, height)


class AntiDetectionManager:
    """Coordinates all anti-detection measures."""

    def __init__(self, config: Optional[AntiDetectionConfig] = None):
        self.config = config or AntiDetectionConfig()
        self.logger = get_logger(__name__)

        # Initialize components
        self.user_agent_rotator = UserAgentRotator(self.config)
        self.header_randomizer = HeaderRandomizer(self.config)
        self.timing_randomizer = TimingRandomizer(self.config)
        self.fingerprint_reducer = FingerprintReducer(self.config)

        # Statistics
        self.requests_processed = 0
        self.detections_avoided = 0

    async def prepare_request(
        self, base_headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Prepare request with anti-detection measures.

        Args:
            base_headers: Base headers to extend

        Returns:
            Dictionary with prepared request data
        """
        # Apply timing delay
        delay_applied = await self.timing_randomizer.apply_delay()

        # Get user-agent
        user_agent = self.user_agent_rotator.get_user_agent()

        # Get randomized headers
        headers = self.header_randomizer.get_randomized_headers(base_headers)
        headers["User-Agent"] = user_agent

        # Get browser configuration
        browser_args = self.fingerprint_reducer.get_browser_args()
        viewport_size = self.fingerprint_reducer.get_viewport_size()

        self.requests_processed += 1

        request_data = {
            "headers": headers,
            "user_agent": user_agent,
            "browser_args": browser_args,
            "viewport_size": viewport_size,
            "delay_applied": delay_applied,
            "profile": self.user_agent_rotator.get_current_profile(),
        }

        self.logger.debug(f"Prepared anti-detection request #{self.requests_processed}")
        return request_data

    def get_statistics(self) -> Dict[str, Any]:
        """Get anti-detection statistics."""
        return {
            "requests_processed": self.requests_processed,
            "detections_avoided": self.detections_avoided,
            "current_user_agent": self.user_agent_rotator.get_current_profile(),
            "config": {
                "user_agent_rotation": self.config.enable_user_agent_rotation,
                "header_randomization": self.config.enable_header_randomization,
                "timing_randomization": self.config.enable_timing_randomization,
                "fingerprint_reduction": self.config.enable_fingerprint_reduction,
            },
        }

    def update_config(self, new_config: AntiDetectionConfig) -> None:
        """Update anti-detection configuration."""
        self.config = new_config

        # Reinitialize components with new config
        self.user_agent_rotator = UserAgentRotator(self.config)
        self.header_randomizer = HeaderRandomizer(self.config)
        self.timing_randomizer = TimingRandomizer(self.config)
        self.fingerprint_reducer = FingerprintReducer(self.config)

        self.logger.info("Anti-detection configuration updated")


# Convenience functions for easy integration
async def create_anti_detection_manager(
    config: Optional[AntiDetectionConfig] = None,
) -> AntiDetectionManager:
    """Create and initialize anti-detection manager."""
    manager = AntiDetectionManager(config)
    logger.info("Anti-detection manager created successfully")
    return manager


def create_stealth_config() -> AntiDetectionConfig:
    """Create configuration optimized for maximum stealth."""
    return AntiDetectionConfig(
        enable_user_agent_rotation=True,
        user_agent_rotation_frequency=3,
        enable_header_randomization=True,
        randomize_accept_language=True,
        randomize_accept_encoding=True,
        randomize_connection_header=True,
        enable_timing_randomization=True,
        min_delay_seconds=2.0,
        max_delay_seconds=5.0,
        human_like_delays=True,
        enable_fingerprint_reduction=True,
        disable_webgl=True,
        disable_canvas_fingerprinting=True,
        randomize_screen_resolution=True,
        enable_request_headers_variation=True,
        max_concurrent_requests=1,  # Most conservative
    )


def create_balanced_config() -> AntiDetectionConfig:
    """Create configuration balancing stealth and performance."""
    return AntiDetectionConfig(
        enable_user_agent_rotation=True,
        user_agent_rotation_frequency=5,
        enable_header_randomization=True,
        randomize_accept_language=True,
        randomize_accept_encoding=True,
        randomize_connection_header=False,
        enable_timing_randomization=True,
        min_delay_seconds=1.0,
        max_delay_seconds=3.0,
        human_like_delays=True,
        enable_fingerprint_reduction=True,
        disable_webgl=False,
        disable_canvas_fingerprinting=True,
        randomize_screen_resolution=True,
        enable_request_headers_variation=True,
        max_concurrent_requests=3,
    )


def create_performance_config() -> AntiDetectionConfig:
    """Create configuration optimized for performance with minimal anti-detection."""
    return AntiDetectionConfig(
        enable_user_agent_rotation=True,
        user_agent_rotation_frequency=10,
        enable_header_randomization=False,
        enable_timing_randomization=False,
        enable_fingerprint_reduction=False,
        max_concurrent_requests=5,
    )
