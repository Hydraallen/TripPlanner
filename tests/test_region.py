from __future__ import annotations

from tripplanner.web.services.region import is_chinese_destination


class TestChineseDetection:
    def test_chinese_characters(self) -> None:
        assert is_chinese_destination("北京") is True
        assert is_chinese_destination("上海") is True

    def test_pinyin_lowercase(self) -> None:
        assert is_chinese_destination("beijing") is True
        assert is_chinese_destination("shanghai") is True

    def test_pinyin_mixed_case(self) -> None:
        assert is_chinese_destination("Beijing") is True
        assert is_chinese_destination("Shanghai") is True
        assert is_chinese_destination("GUANGZHOU") is True

    def test_pinyin_with_whitespace(self) -> None:
        assert is_chinese_destination("  beijing  ") is True

    def test_international_cities(self) -> None:
        assert is_chinese_destination("Tokyo") is False
        assert is_chinese_destination("Paris") is False
        assert is_chinese_destination("New York") is False
        assert is_chinese_destination("London") is False

    def test_less_common_chinese_cities(self) -> None:
        assert is_chinese_destination("sanya") is True
        assert is_chinese_destination("三亚") is True
        assert is_chinese_destination("lijiang") is True
        assert is_chinese_destination("丽江") is True
