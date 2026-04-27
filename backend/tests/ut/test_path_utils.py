"""Unit tests for app.core.utils path helpers."""

from app.core.utils import (
    sanitize_path_segment,
    sanitize_org_name,
    sanitize_upload_basename,
)


def test_sanitize_path_segment_none_and_empty() -> None:
    assert sanitize_path_segment(None) == "unknown"
    assert sanitize_path_segment("") == "unknown"


def test_sanitize_path_segment_basic() -> None:
    assert sanitize_path_segment("Acme Corp") == "acme-corp"
    assert sanitize_path_segment("  x  ") == "x"
    # dangerous segments are neutralized, not path-traversed
    out = sanitize_path_segment("a/../b")
    assert ".." not in out


def test_sanitize_org_name_is_same_as_path_segment() -> None:
    assert sanitize_org_name is sanitize_path_segment


def test_sanitize_upload_basename_uses_basename_and_caps_length() -> None:
    assert sanitize_upload_basename("foo/../bar.png") == "bar.png"
    s = sanitize_upload_basename("My Photo!.png")
    assert s.endswith("png")
    long_name = "a" * 300 + ".png"
    assert len(sanitize_upload_basename(long_name)) == 200


def test_sanitize_upload_basename_strips_to_image() -> None:
    assert sanitize_upload_basename("...") == "image"
