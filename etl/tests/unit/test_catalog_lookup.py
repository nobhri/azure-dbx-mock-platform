"""Unit tests for mock_platform.catalog_lookup."""

import pytest

from mock_platform.catalog_lookup import get_catalog


class TestGetCatalog:
    def test_dev_returns_mock(self):
        assert get_catalog("dev") == "mock"

    def test_prod_returns_mock(self):
        assert get_catalog("prod") == "mock"

    def test_unknown_env_raises(self):
        with pytest.raises(ValueError, match="Unknown environment 'staging'"):
            get_catalog("staging")

    def test_empty_string_raises(self):
        with pytest.raises(ValueError, match="Unknown environment ''"):
            get_catalog("")

    def test_case_sensitive(self):
        with pytest.raises(ValueError, match="Unknown environment 'Dev'"):
            get_catalog("Dev")
