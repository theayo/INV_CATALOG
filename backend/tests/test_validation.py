import pytest

from app.catalog import CatalogError, validate_photo


def test_real_image_is_accepted(photo):
    assert validate_photo(photo, 1024) == "image/png"


@pytest.mark.parametrize("contents", [b"", b"not an image", b"<svg></svg>"])
def test_fake_images_are_rejected(contents):
    with pytest.raises(CatalogError):
        validate_photo(contents, 1024)


def test_size_limit_is_enforced(photo):
    with pytest.raises(CatalogError):
        validate_photo(photo, len(photo) - 1)
