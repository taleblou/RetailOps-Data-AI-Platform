from core.ingestion.base.mapper import ColumnMapper


def test_mapper_detects_aliases_and_required_columns() -> None:
    mapper = ColumnMapper()
    result = mapper.build_mapping(
        source_columns=["Order ID", "qty", "price_each"],
        required_columns=["order_id", "quantity", "unit_price"],
    )
    targets = {item.target for item in result.mappings}
    assert {"order_id", "quantity", "unit_price"}.issubset(targets)
    assert result.missing_required == []
