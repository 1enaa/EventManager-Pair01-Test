
def test_sample_participant_fixture(sample_participant_dict):
    """Check that the participant fixture works."""
    assert sample_participant_dict["name"] == "Amine"
    assert sample_participant_dict["email"] == "amine@example.com"


def test_participant_name_is_not_empty(sample_participant_dict):
    """Check that the sample participant has a name."""
    assert len(sample_participant_dict["name"]) >= 2


def test_participant_email_contains_at_symbol(sample_participant_dict):
    """Basic check of the sample participant email."""
    assert "@" in sample_participant_dict["email"]
