from core.ingestion.base.validator import DataValidator


def test_validator_detects_missing_and_duplicate_values() -> None:
    validator = DataValidator()
    result = validator.validate(
        rows=[
            {"order_id": "1001", "quantity": "1"},
            {"order_id": "1001", "quantity": ""},
        ],
        required_columns=["order_id", "quantity"],
        type_hints={"quantity": "int"},
        unique_key_columns=["order_id"],
    )
    assert not result.valid
    codes = {issue.code for issue in result.errors}
    assert "required_missing" in codes
    assert "duplicate_key" in codes
