import pytest

from conda_store_server._internal import schema


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("Viewer", schema.Role.VIEWER),
        ("editor", schema.Role.EDITOR),
        ("ADMIN", schema.Role.ADMIN),
        ((0, "viewer"), schema.Role.VIEWER),
        ((1, "editor"), schema.Role.EDITOR),
        ((2, "admin"), schema.Role.ADMIN),
    ],
)
def test_valid_role(value, expected):
    """Test that valid Role values instantiate correctly."""
    assert schema.Role(value) == expected


@pytest.mark.parametrize(
    ("value"),
    [
        ("foo"),
        (2, "viewer"),
    ],
)
def test_invalid_role(value):
    """Test that invalid Role values raise an exception."""
    with pytest.Raises(ValueError):
        schema.Role(value)


def test_deprecated_role():
    """Test that 'developer' is a deprecated alias to 'editor'."""
    with pytest.deprecated_call():
        assert schema.Role("developer") == schema.Role.EDITOR


def test_role_rankings():
    """Test that Role object comparisons work as intended."""
    assert schema.Role.VIEWER < schema.Role.EDITOR < schema.Role.ADMIN
    assert schema.Role.ADMIN > schema.Role.EDITOR > schema.Role.VIEWER
    assert schema.Role.VIEWER == schema.Role.VIEWER
    assert schema.Role.EDITOR == schema.Role.EDITOR
    assert schema.Role.ADMIN == schema.Role.ADMIN
