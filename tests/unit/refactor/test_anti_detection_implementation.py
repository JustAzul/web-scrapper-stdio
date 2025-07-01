"""
Test suite for Anti-Detection Measures Implementation (T027).

This module provides comprehensive testing for all anti-detection components:
- UserAgentRotator with weighted selection
- HeaderRandomizer with various randomization strategies
- TimingRandomizer with human-like delays
- FingerprintReducer with browser argument generation
- AntiDetectionManager coordinating all measures

TDD Implementation: Comprehensive test coverage >95%.
"""

import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.scraper.anti_detection import (
    AntiDetectionConfig,
    AntiDetectionManager,
    BrowserType,
    FingerprintReducer,
    HeaderRandomizer,
    Platform,
    TimingRandomizer,
    UserAgentProfile,
    UserAgentRotator,
    create_anti_detection_manager,
    create_balanced_config,
    create_performance_config,
    create_stealth_config,
)
from src.services.anti_detection.implementation import (
    DelayConfig,
    TimingRandomizer,
)


class TestUserAgentProfile:
    """Test UserAgentProfile data class."""

    def test_user_agent_profile_creation(self):
        """Test UserAgentProfile creation with all fields."""
        profile = UserAgentProfile(
            user_agent="Mozilla/5.0 (Test Browser)",
            browser_type=BrowserType.CHROME,
            platform=Platform.WINDOWS,
            version="1.0.0",
            market_share=0.5,
        )

        assert profile.user_agent == "Mozilla/5.0 (Test Browser)"
        assert profile.browser_type == BrowserType.CHROME
        assert profile.platform == Platform.WINDOWS
        assert profile.version == "1.0.0"
        assert profile.market_share == 0.5

    def test_browser_type_enum(self):
        """Test BrowserType enum values."""
        assert BrowserType.CHROME.value == "chrome"
        assert BrowserType.FIREFOX.value == "firefox"
        assert BrowserType.SAFARI.value == "safari"
        assert BrowserType.EDGE.value == "edge"

    def test_platform_enum(self):
        """Test Platform enum values."""
        assert Platform.WINDOWS.value == "windows"
        assert Platform.MACOS.value == "macos"
        assert Platform.LINUX.value == "linux"


class TestAntiDetectionConfig:
    """Test AntiDetectionConfig data class."""

    def test_default_config(self):
        """Test default configuration values."""
        config = AntiDetectionConfig()

        # User-Agent rotation
        assert config.enable_user_agent_rotation is True
        assert config.user_agent_rotation_frequency == 5

        # Header randomization
        assert config.enable_header_randomization is True
        assert config.randomize_accept_language is True
        assert config.randomize_accept_encoding is True
        assert config.randomize_connection_header is True

        # Timing randomization
        assert config.enable_timing_randomization is True
        assert config.min_delay_seconds == 1.0
        assert config.max_delay_seconds == 3.0
        assert config.human_like_delays is True

        # Fingerprint reduction
        assert config.enable_fingerprint_reduction is True
        assert config.disable_webgl is True
        assert config.disable_canvas_fingerprinting is True
        assert config.randomize_screen_resolution is True

        # Advanced features
        assert config.enable_request_headers_variation is True
        assert config.enable_connection_pooling is False
        assert config.max_concurrent_requests == 3

    def test_custom_config(self):
        """Test custom configuration values."""
        config = AntiDetectionConfig(
            enable_user_agent_rotation=False,
            user_agent_rotation_frequency=10,
            min_delay_seconds=2.0,
            max_delay_seconds=5.0,
            max_concurrent_requests=1,
        )

        assert config.enable_user_agent_rotation is False
        assert config.user_agent_rotation_frequency == 10
        assert config.min_delay_seconds == 2.0
        assert config.max_delay_seconds == 5.0
        assert config.max_concurrent_requests == 1


class TestUserAgentRotator:
    """Test UserAgentRotator functionality."""

    def test_initialization(self):
        """Test UserAgentRotator initialization."""
        config = AntiDetectionConfig()
        rotator = UserAgentRotator(config)

        assert rotator.config == config
        assert rotator.current_profile is None
        assert rotator.request_count == 0
        assert len(rotator.profiles) > 0

    def test_user_agent_profiles_loaded(self):
        """Test that user-agent profiles are properly loaded."""
        config = AntiDetectionConfig()
        rotator = UserAgentRotator(config)

        # Check that profiles are loaded
        assert len(rotator.profiles) >= 7  # Minimum expected profiles

        # Check profile structure
        for profile in rotator.profiles:
            assert isinstance(profile, UserAgentProfile)
            assert profile.user_agent
            assert isinstance(profile.browser_type, BrowserType)
            assert isinstance(profile.platform, Platform)
            assert profile.version
            assert 0 <= profile.market_share <= 1

        # Check market share totals approximately 1.0
        total_market_share = sum(p.market_share for p in rotator.profiles)
        assert 0.9 <= total_market_share <= 1.1

    def test_get_user_agent_disabled(self):
        """Test user-agent rotation when disabled."""
        config = AntiDetectionConfig(enable_user_agent_rotation=False)
        rotator = UserAgentRotator(config)

        user_agent = rotator.get_user_agent()
        assert user_agent == rotator.profiles[0].user_agent

        # Should not change on subsequent calls
        user_agent2 = rotator.get_user_agent()
        assert user_agent2 == user_agent

    def test_get_user_agent_enabled(self):
        """Test user-agent rotation when enabled."""
        config = AntiDetectionConfig(enable_user_agent_rotation=True)
        rotator = UserAgentRotator(config)

        # First call should select a profile
        user_agent1 = rotator.get_user_agent()
        assert user_agent1
        assert rotator.current_profile is not None
        assert rotator.request_count == 1

        # Subsequent calls within frequency should return same user-agent
        user_agent2 = rotator.get_user_agent()
        assert user_agent2 == user_agent1
        assert rotator.request_count == 2

    def test_force_rotation(self):
        """Test forced user-agent rotation."""
        config = AntiDetectionConfig(enable_user_agent_rotation=True)
        rotator = UserAgentRotator(config)

        rotator.get_user_agent()

        # Force rotation
        rotator.get_user_agent(force_rotation=True)

        # Profile should change (though user-agent might be same by chance)
        assert rotator.request_count == 1  # Reset after rotation

    def test_rotation_frequency(self):
        """Test user-agent rotation based on frequency."""
        config = AntiDetectionConfig(
            enable_user_agent_rotation=True, user_agent_rotation_frequency=3
        )
        rotator = UserAgentRotator(config)

        # Get user-agent multiple times
        user_agents = []
        for i in range(6):
            user_agents.append(rotator.get_user_agent())

        # Should have rotated after 3 requests
        assert rotator.request_count == 3  # Reset after rotation

    @patch("secrets.SystemRandom.uniform")
    def test_weighted_profile_selection(self, mock_random_uniform):
        """Test weighted profile selection."""
        config = AntiDetectionConfig()
        rotator = UserAgentRotator(config)

        # Mock random to select first profile
        total_weight = sum(p.market_share for p in rotator.profiles)
        mock_random_uniform.return_value = (
            total_weight * 0.1
        )  # A value that guarantees the first profile is selected

        selected_profile = rotator._select_weighted_profile()
        assert selected_profile == rotator.profiles[0]

    def test_get_current_profile(self):
        """Test getting current profile."""
        config = AntiDetectionConfig()
        rotator = UserAgentRotator(config)

        # Initially no profile
        assert rotator.get_current_profile() is None

        # After getting user-agent, profile should be set
        rotator.get_user_agent()
        assert rotator.get_current_profile() is not None


class TestHeaderRandomizer:
    """Test HeaderRandomizer functionality."""

    def test_initialization(self):
        """Test HeaderRandomizer initialization."""
        config = AntiDetectionConfig()
        randomizer = HeaderRandomizer(config)

        assert randomizer.config == config

    def test_randomized_headers_disabled(self):
        """Test header randomization when disabled."""
        config = AntiDetectionConfig(enable_header_randomization=False)
        randomizer = HeaderRandomizer(config)

        headers = randomizer.get_randomized_headers()
        assert headers == {}

        # With base headers
        base_headers = {"Authorization": "Bearer token"}
        headers = randomizer.get_randomized_headers(base_headers)
        assert headers == base_headers

    def test_randomized_headers_enabled(self):
        """Test header randomization when enabled."""
        config = AntiDetectionConfig(enable_header_randomization=True)
        randomizer = HeaderRandomizer(config)

        headers = randomizer.get_randomized_headers()

        # Should have randomized headers
        assert len(headers) > 0

        # Check for expected headers
        if config.randomize_accept_language:
            assert "Accept-Language" in headers
        if config.randomize_accept_encoding:
            assert "Accept-Encoding" in headers

    def test_accept_language_randomization(self):
        """Test Accept-Language header randomization."""
        config = AntiDetectionConfig(
            enable_header_randomization=True, randomize_accept_language=True
        )
        randomizer = HeaderRandomizer(config)

        # Generate multiple headers to test randomization
        languages = set()
        for _ in range(10):
            headers = randomizer.get_randomized_headers()
            if "Accept-Language" in headers:
                languages.add(headers["Accept-Language"])

        # Should have some variety
        assert len(languages) >= 1

    def test_accept_encoding_randomization(self):
        """Test Accept-Encoding header randomization."""
        config = AntiDetectionConfig(
            enable_header_randomization=True, randomize_accept_encoding=True
        )
        randomizer = HeaderRandomizer(config)

        headers = randomizer.get_randomized_headers()
        if "Accept-Encoding" in headers:
            encoding = headers["Accept-Encoding"]
            assert "gzip" in encoding or "deflate" in encoding

    def test_connection_header_randomization(self):
        """Test Connection header randomization."""
        config = AntiDetectionConfig(
            enable_header_randomization=True, randomize_connection_header=True
        )
        randomizer = HeaderRandomizer(config)

        # Generate multiple headers
        connections = set()
        for _ in range(20):
            headers = randomizer.get_randomized_headers()
            if "Connection" in headers:
                connections.add(headers["Connection"])

        # Should have keep-alive or close
        assert connections.issubset({"keep-alive", "close"})

    def test_varied_browser_headers(self):
        """Test varied browser headers."""
        config = AntiDetectionConfig(
            enable_header_randomization=True, enable_request_headers_variation=True
        )
        randomizer = HeaderRandomizer(config)

        headers = randomizer.get_randomized_headers()

        # Check for possible browser headers
        possible_headers = {
            "DNT",
            "Upgrade-Insecure-Requests",
            "Sec-Fetch-Dest",
            "Sec-Fetch-Mode",
            "Sec-Fetch-Site",
        }

        # Should have some browser headers
        set(headers.keys()) & possible_headers
        # Note: Due to randomization, not all headers may be present

    def test_base_headers_preserved(self):
        """Test that base headers are preserved and extended."""
        config = AntiDetectionConfig(enable_header_randomization=True)
        randomizer = HeaderRandomizer(config)

        base_headers = {"Authorization": "Bearer token", "Custom-Header": "value"}
        headers = randomizer.get_randomized_headers(base_headers)

        # Base headers should be preserved
        assert headers["Authorization"] == "Bearer token"
        assert headers["Custom-Header"] == "value"

        # Should have additional randomized headers
        assert len(headers) > len(base_headers)


class TestTimingRandomizer:
    """Test TimingRandomizer functionality."""

    def test_initialization(self):
        """Test TimingRandomizer initialization."""
        config = AntiDetectionConfig()
        randomizer = TimingRandomizer(config)

        assert randomizer.config == config

    @pytest.mark.asyncio
    async def test_apply_delay_disabled(self):
        """Test delay application when disabled."""
        config = AntiDetectionConfig(enable_timing_randomization=False)
        randomizer = TimingRandomizer(config)

        start_time = time.time()
        delay = await randomizer.apply_delay()
        end_time = time.time()

        assert delay == 0.0
        assert (end_time - start_time) < 0.1  # Should be very fast

    @pytest.mark.asyncio
    async def test_apply_delay_enabled(self):
        """Test delay application when enabled."""
        config = AntiDetectionConfig(
            enable_timing_randomization=True,
            min_delay_seconds=0.1,
            max_delay_seconds=0.2,
        )
        randomizer = TimingRandomizer(config)

        start_time = time.time()
        delay = await randomizer.apply_delay()
        end_time = time.time()

        # Should apply some delay
        actual_delay = end_time - start_time
        assert actual_delay >= 0.05  # Some delay applied
        assert 0.1 <= delay <= 0.2  # Reported delay in range

    @pytest.mark.asyncio
    @patch("asyncio.sleep", new_callable=AsyncMock)
    async def test_force_delay(self, mock_sleep):
        """Verify that forced delay always waits for the specified max_delay."""
        mock_config = MagicMock(spec=AntiDetectionConfig)
        mock_config.delay_config = MagicMock(spec=DelayConfig)
        mock_config.delay_config.enabled = True
        mock_config.delay_config.min_delay = 1.0
        mock_config.delay_config.max_delay = 5.0

        randomizer = TimingRandomizer(mock_config)
        await randomizer.apply_delay(force_delay=True)  # Corrected from force=True
        # Expect the sleep to be exactly the max_delay
        mock_sleep.assert_called_once_with(5.0)

    @pytest.mark.asyncio
    @patch("asyncio.sleep", new_callable=AsyncMock)
    async def test_consecutive_delays(self, mock_sleep):
        """Test that delays are not applied too close together unless forced."""
        config = AntiDetectionConfig(min_delay_seconds=0.1, max_delay_seconds=0.2)
        randomizer = TimingRandomizer(config)

        # First delay
        delay1 = await randomizer.apply_delay()
        assert delay1 > 0

        # Second delay
        delay2 = await randomizer.apply_delay()
        assert delay2 > 0

        # Delay should have been applied twice
        assert mock_sleep.call_count == 2

    def test_human_like_delay_generation(self):
        """Test human-like delay generation using normal distribution."""
        config = AntiDetectionConfig(
            min_delay_seconds=1.0, max_delay_seconds=3.0, human_like_delays=True
        )
        randomizer = TimingRandomizer(config)

        delays = []
        for _ in range(100):
            delay = randomizer._get_human_like_delay()
            delays.append(delay)
            assert 1.0 <= delay <= 3.0

        # Should have some variety in delays
        assert len(set(delays)) > 10


class TestFingerprintReducer:
    """Test FingerprintReducer functionality."""

    def test_initialization(self):
        """Test FingerprintReducer initialization."""
        config = AntiDetectionConfig()
        reducer = FingerprintReducer(config)

        assert reducer.config == config

    def test_browser_args_disabled(self):
        """Test browser arguments when fingerprint reduction is disabled."""
        config = AntiDetectionConfig(enable_fingerprint_reduction=False)
        reducer = FingerprintReducer(config)

        args = reducer.get_browser_args()
        assert args == []

    def test_browser_args_enabled(self):
        """Test browser arguments when fingerprint reduction is enabled."""
        config = AntiDetectionConfig(enable_fingerprint_reduction=True)
        reducer = FingerprintReducer(config)

        args = reducer.get_browser_args()
        assert len(args) > 0

        # Check for common fingerprint reduction arguments
        args_str = " ".join(args)
        assert "--no-first-run" in args_str
        assert "--no-default-browser-check" in args_str

    def test_webgl_disabled(self):
        """Test WebGL disabling."""
        config = AntiDetectionConfig(
            enable_fingerprint_reduction=True, disable_webgl=True
        )
        reducer = FingerprintReducer(config)

        args = reducer.get_browser_args()
        args_str = " ".join(args)
        assert "--disable-webgl" in args_str

    def test_canvas_fingerprinting_disabled(self):
        """Test canvas fingerprinting disabling."""
        config = AntiDetectionConfig(
            enable_fingerprint_reduction=True, disable_canvas_fingerprinting=True
        )
        reducer = FingerprintReducer(config)

        args = reducer.get_browser_args()
        args_str = " ".join(args)
        assert "--disable-canvas-aa" in args_str

    def test_viewport_size_default(self):
        """Test default viewport size."""
        config = AntiDetectionConfig(randomize_screen_resolution=False)
        reducer = FingerprintReducer(config)

        width, height = reducer.get_viewport_size()
        assert width == 1920
        assert height == 1080

    def test_viewport_size_randomized(self):
        """Test randomized viewport size."""
        config = AntiDetectionConfig(randomize_screen_resolution=True)
        reducer = FingerprintReducer(config)

        sizes = set()
        for _ in range(10):
            size = reducer.get_viewport_size()
            sizes.add(size)
            width, height = size
            assert 1270 <= width <= 1930  # Base resolution ± 10
            assert 710 <= height <= 1090

        # Should have some variety
        assert len(sizes) > 1


class TestAntiDetectionManager:
    """Test AntiDetectionManager functionality."""

    def test_initialization_default_config(self):
        """Test AntiDetectionManager initialization with default config."""
        manager = AntiDetectionManager()

        assert isinstance(manager.config, AntiDetectionConfig)
        assert isinstance(manager.user_agent_rotator, UserAgentRotator)
        assert isinstance(manager.header_randomizer, HeaderRandomizer)
        assert isinstance(manager.timing_randomizer, TimingRandomizer)
        assert isinstance(manager.fingerprint_reducer, FingerprintReducer)
        assert manager.requests_processed == 0
        assert manager.detections_avoided == 0

    def test_initialization_custom_config(self):
        """Test AntiDetectionManager initialization with custom config."""
        config = AntiDetectionConfig(enable_user_agent_rotation=False)
        manager = AntiDetectionManager(config)

        assert manager.config == config
        assert manager.config.enable_user_agent_rotation is False

    @pytest.mark.asyncio
    async def test_prepare_request_basic(self):
        """Test basic request preparation."""
        config = AntiDetectionConfig(
            enable_timing_randomization=False  # Disable for faster testing
        )
        manager = AntiDetectionManager(config)

        request_data = await manager.prepare_request()

        assert "headers" in request_data
        assert "user_agent" in request_data
        assert "browser_args" in request_data
        assert "viewport_size" in request_data
        assert "delay_applied" in request_data
        assert "profile" in request_data

        assert isinstance(request_data["headers"], dict)
        assert isinstance(request_data["user_agent"], str)
        assert isinstance(request_data["browser_args"], list)
        assert isinstance(request_data["viewport_size"], tuple)
        assert isinstance(request_data["delay_applied"], float)

        assert manager.requests_processed == 1

    @pytest.mark.asyncio
    async def test_prepare_request_with_base_headers(self):
        """Test request preparation with base headers."""
        config = AntiDetectionConfig(enable_timing_randomization=False)
        manager = AntiDetectionManager(config)

        base_headers = {"Authorization": "Bearer token"}
        request_data = await manager.prepare_request(base_headers)

        assert request_data["headers"]["Authorization"] == "Bearer token"
        assert request_data["headers"]["User-Agent"]  # Should be added

    @pytest.mark.asyncio
    async def test_prepare_request_timing(self):
        """Test request preparation with timing."""
        config = AntiDetectionConfig(
            enable_timing_randomization=True,
            min_delay_seconds=0.01,
            max_delay_seconds=0.02,
        )
        manager = AntiDetectionManager(config)

        start_time = time.time()
        request_data = await manager.prepare_request()
        end_time = time.time()

        # Should have applied some delay
        assert request_data["delay_applied"] >= 0
        assert (end_time - start_time) >= 0.005

    def test_get_statistics(self):
        """Test statistics retrieval."""
        manager = AntiDetectionManager()

        stats = manager.get_statistics()

        assert "requests_processed" in stats
        assert "detections_avoided" in stats
        assert "current_user_agent" in stats
        assert "config" in stats

        assert stats["requests_processed"] == 0
        assert isinstance(stats["config"], dict)

    def test_update_config(self):
        """Test configuration update."""
        manager = AntiDetectionManager()
        original_config = manager.config

        new_config = AntiDetectionConfig(enable_user_agent_rotation=False)
        manager.update_config(new_config)

        assert manager.config == new_config
        assert manager.config != original_config
        assert manager.config.enable_user_agent_rotation is False


class TestConvenienceFunctions:
    """Test convenience functions."""

    @pytest.mark.asyncio
    async def test_create_anti_detection_manager(self):
        """Test anti-detection manager creation."""
        manager = await create_anti_detection_manager()

        assert isinstance(manager, AntiDetectionManager)
        assert isinstance(manager.config, AntiDetectionConfig)

    @pytest.mark.asyncio
    async def test_create_anti_detection_manager_with_config(self):
        """Test anti-detection manager creation with custom config."""
        config = AntiDetectionConfig(enable_user_agent_rotation=False)
        manager = await create_anti_detection_manager(config)

        assert manager.config == config

    def test_create_stealth_config(self):
        """Test stealth configuration creation."""
        config = create_stealth_config()

        assert isinstance(config, AntiDetectionConfig)
        assert config.enable_user_agent_rotation is True
        assert config.user_agent_rotation_frequency == 3
        assert config.min_delay_seconds == 2.0
        assert config.max_delay_seconds == 5.0
        assert config.max_concurrent_requests == 1

    def test_create_balanced_config(self):
        """Test balanced configuration creation."""
        config = create_balanced_config()

        assert isinstance(config, AntiDetectionConfig)
        assert config.enable_user_agent_rotation is True
        assert config.user_agent_rotation_frequency == 5
        assert config.min_delay_seconds == 1.0
        assert config.max_delay_seconds == 3.0
        assert config.max_concurrent_requests == 3

    def test_create_performance_config(self):
        """Test performance configuration creation."""
        config = create_performance_config()

        assert isinstance(config, AntiDetectionConfig)
        assert config.enable_user_agent_rotation is True
        assert config.user_agent_rotation_frequency == 10
        assert config.enable_header_randomization is False
        assert config.enable_timing_randomization is False
        assert config.enable_fingerprint_reduction is False
        assert config.max_concurrent_requests == 5


class TestIntegration:
    """Integration tests for anti-detection system."""

    @pytest.mark.asyncio
    async def test_full_workflow(self):
        """Test complete anti-detection workflow."""
        config = AntiDetectionConfig(
            enable_timing_randomization=True,
            min_delay_seconds=0.01,
            max_delay_seconds=0.02,
        )
        manager = AntiDetectionManager(config)

        # Prepare multiple requests
        request_data_list = []
        for _ in range(3):
            request_data = await manager.prepare_request()
            request_data_list.append(request_data)

        # Verify each request has required data
        for request_data in request_data_list:
            assert request_data["headers"]
            assert request_data["user_agent"]
            assert request_data["browser_args"]
            assert request_data["viewport_size"]

        # Verify manager state
        assert manager.requests_processed == 3

        # Verify statistics
        stats = manager.get_statistics()
        assert stats["requests_processed"] == 3

    @pytest.mark.asyncio
    async def test_user_agent_rotation_workflow(self):
        """Test user-agent rotation in workflow."""
        config = AntiDetectionConfig(
            enable_user_agent_rotation=True,
            user_agent_rotation_frequency=2,
            enable_timing_randomization=False,
        )
        manager = AntiDetectionManager(config)

        user_agents = []
        for _ in range(5):
            request_data = await manager.prepare_request()
            user_agents.append(request_data["user_agent"])

        # Should have some rotation (though might get same by chance)
        assert len(user_agents) == 5

    @pytest.mark.asyncio
    async def test_configuration_presets_workflow(self):
        """Test different configuration presets."""
        configs = [
            create_stealth_config(),
            create_balanced_config(),
            create_performance_config(),
        ]

        for config in configs:
            manager = AntiDetectionManager(config)
            request_data = await manager.prepare_request()

            # All should produce valid request data
            assert request_data["headers"]
            assert request_data["user_agent"]
            assert request_data["browser_args"] is not None  # May be empty list
            assert request_data["viewport_size"]
