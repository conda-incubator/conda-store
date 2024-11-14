import pytest

from conda_store_server._internal import schema


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("NoNe", schema.Role.NONE),
        ("Viewer", schema.Role.VIEWER),
        ("editor", schema.Role.EDITOR),
        ("ADMIN", schema.Role.ADMIN),
        ((0, "none"), schema.Role.NONE),
        ((1, "viewer"), schema.Role.VIEWER),
        ((2, "editor"), schema.Role.EDITOR),
        ((3, "admin"), schema.Role.ADMIN),
    ],
)
def test_valid_role(value, expected):
    """Test that valid Role values instantiate correctly."""
    assert schema.Role(value) == expected


@pytest.mark.parametrize(
    ("value"),
    [
        ("foo"),
        (5, "viewer"),
    ],
)
def test_invalid_role(value):
    """Test that invalid Role values raise an exception."""
    with pytest.raises(ValueError):
        schema.Role(value)


def test_deprecated_role():
    """Test that 'developer' is a deprecated alias to 'editor'."""
    with pytest.deprecated_call():
        assert schema.Role("developer") == schema.Role.EDITOR


def test_role_rankings():
    """Test that Role object comparisons work as intended."""
    assert (
        schema.Role.NONE < schema.Role.VIEWER < schema.Role.EDITOR < schema.Role.ADMIN
    )
    assert (
        schema.Role.ADMIN > schema.Role.EDITOR > schema.Role.VIEWER > schema.Role.NONE
    )
    assert schema.Role.NONE == schema.Role.NONE
    assert schema.Role.VIEWER == schema.Role.VIEWER
    assert schema.Role.EDITOR == schema.Role.EDITOR
    assert schema.Role.ADMIN == schema.Role.ADMIN


@pytest.mark.parametrize(
    ("roles", "expected"),
    [
        (["none"], schema.Role.NONE),
        (["none", "editor"], schema.Role.EDITOR),
        (["none", "viewer"], schema.Role.VIEWER),
        (["viewer", "editor"], schema.Role.EDITOR),
        (["viewer", "editor", "admin"], schema.Role.ADMIN),
        (["viewer", "admin"], schema.Role.ADMIN),
        (["editor", "admin"], schema.Role.ADMIN),
        (["viewer"], schema.Role.VIEWER),
        (["editor", "editor"], schema.Role.EDITOR),
    ],
)
def test_max_role(roles, expected):
    """Test that the max_role returns the highest Role."""
    assert schema.Role.max_role(roles) == expected
