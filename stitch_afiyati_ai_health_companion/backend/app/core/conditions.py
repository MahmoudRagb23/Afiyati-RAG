from __future__ import annotations

from collections.abc import Iterable


SUPPORTED_CONDITIONS = ("hypertension", "type_2_diabetes")
SUPPORTED_CONDITION_SET = frozenset(SUPPORTED_CONDITIONS)


def supported_conditions(values: Iterable[str] | None) -> list[str]:
    return list(
        dict.fromkeys(
            value for value in (values or []) if value in SUPPORTED_CONDITION_SET
        )
    )


def is_supported_condition(value: object) -> bool:
    return isinstance(value, str) and value in SUPPORTED_CONDITION_SET
