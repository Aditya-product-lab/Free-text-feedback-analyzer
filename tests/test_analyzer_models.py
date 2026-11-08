from typing import get_args
from pydantic import ValidationError

from analyzer import BatchClassification, ClassifiedFeedback, PrimaryTag, SecondaryTag
from utils import PRIMARY_TAGS, SECONDARY_TAGS


def test_tag_definitions_consistency():
    """Ensure PrimaryTag and SecondaryTag literals match the tags defined in utils.py."""
    expected_primary = set(get_args(PrimaryTag))
    assert set(PRIMARY_TAGS.keys()) == expected_primary, (
        f"Mismatch between PrimaryTag literal and PRIMARY_TAGS: "
        f"diff={set(PRIMARY_TAGS.keys()) ^ expected_primary}"
    )

    expected_secondary = set(get_args(SecondaryTag))
    assert set(SECONDARY_TAGS) == expected_secondary, (
        f"Mismatch between SecondaryTag literal and SECONDARY_TAGS: "
        f"diff={set(SECONDARY_TAGS) ^ expected_secondary}"
    )


def test_structured_models_valid():
    """Test model validation with each supported tag."""
    items = []
    # Test all primary tags with a valid secondary tag
    for idx, primary in enumerate(get_args(PrimaryTag)):
        items.append(
            ClassifiedFeedback(
                row_index=idx,
                primary_tag=primary,
                secondary_tag="UI/UX",
            )
        )
    # Test all secondary tags with a valid primary tag
    offset = len(items)
    for idx, secondary in enumerate(get_args(SecondaryTag)):
        items.append(
            ClassifiedFeedback(
                row_index=offset + idx,
                primary_tag="Bug",
                secondary_tag=secondary,
            )
        )

    batch = BatchClassification(items=items)
    assert len(batch.items) == len(get_args(PrimaryTag)) + len(get_args(SecondaryTag))
    assert batch.items[4].primary_tag == "Compliment"


def test_structured_models_invalid_primary():
    """Invalid primary tag should raise a ValidationError."""
    try:
        ClassifiedFeedback(
            row_index=0,
            primary_tag="InvalidTag",
            secondary_tag="UI/UX",
        )
    except ValidationError:
        return
    assert False, "Expected ValidationError was not raised for invalid primary tag"


def test_structured_models_invalid_secondary():
    """Invalid secondary tag should raise a ValidationError."""
    try:
        ClassifiedFeedback(
            row_index=0,
            primary_tag="Bug",
            secondary_tag="InvalidSecondary",
        )
    except ValidationError:
        return
    assert False, "Expected ValidationError was not raised for invalid secondary tag"
