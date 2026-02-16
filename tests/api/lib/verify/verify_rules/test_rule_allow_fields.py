from typing import cast
import pytest

if __name__ == "__main__":
    pytest.main([__file__])

from src.template.front_mater_meta import FrontMatterMeta
from api.lib.verify.verify_rules.rule_allow_fields import RuleAllowFields
from api.lib.util.result import Result


@pytest.mark.parametrize(
    "role",
    [
        "roles_authority",
        "roles_visibility",
        "roles_function",
        "roles_action",
    ],
)
def test_rule_allow_roles(role: str, get_template_fm, get_template_registry):
    template_type = "glyph"
    registry = cast(dict, get_template_registry(template_type))
    reg_fields = cast(dict, registry.get("fields", {}))
    reg_role = cast(dict, reg_fields.get(role, {}))
    reg_allowed_values = cast(list, reg_role.get("allowed_values", []))
    if not reg_allowed_values:
        raise Exception(
            f"Missing allowed values for {role} in registry",
            f"{role}.allowed_values",
        )
    # allowed_values_set = set(reg_allowed_values)
    fm = cast(FrontMatterMeta, get_template_fm(template_type))
    if not fm.has_field(role):
        raise Exception(
            f"Missing {role} field in frontmatter",
            role,
        )
    fm.set_field(role, reg_allowed_values)

    rule = RuleAllowFields(field=role, match_kind="all")
    result = rule.validate(fm, registry)
    assert Result.is_success(result)

    # test with only one allowed value in the list but require all match kind
    fm.set_field(role, [reg_allowed_values[0]])
    rule = RuleAllowFields(field=role, match_kind="all")
    result = rule.validate(fm, registry)
    assert Result.is_failure(result)

    # test with only one allowed value in the list and any match kind
    rule = RuleAllowFields(field=role, match_kind="any")
    result = rule.validate(fm, registry)
    assert Result.is_success(result)

    # test with a value that is not in the allowed values list
    fm.set_field(role, ["not_allowed_value"])
    rule = RuleAllowFields(field=role, match_kind="any")
    result = rule.validate(fm, registry)
    assert Result.is_failure(result)

    # test with an empty list and any match kind with no roles
    fm.set_field(role, [])
    rule = RuleAllowFields(field=role, match_kind="any")
    result = rule.validate(fm, registry)
    assert Result.is_failure(result)


def test_rule_allow_tier(get_template_fm, get_template_registry):
    template_type = "glyph"
    field = "tier"
    # Current expected allowed_values: council, public, family
    registry = cast(dict, get_template_registry(template_type))
    reg_fields = cast(dict, registry.get("fields", {}))
    reg_role = cast(dict, reg_fields.get(field, {}))
    reg_allowed_values = cast(list, reg_role.get("allowed_values", []))
    if not reg_allowed_values:
        raise Exception(
            f"Missing allowed values for {field} in registry",
            f"{field}.allowed_values",
        )
    # allowed_values_set = set(reg_allowed_values)
    fm = cast(FrontMatterMeta, get_template_fm(template_type))
    if not fm.has_field(field):
        raise Exception(
            f"Missing {field} field in frontmatter",
            field,
        )

    fm.set_field(field, reg_allowed_values[0])
    rule = RuleAllowFields(field=field)
    result = rule.validate(fm, registry)
    assert Result.is_success(result)

    fm.set_field(field, "not_allowed_value")
    rule = RuleAllowFields(field=field)
    result = rule.validate(fm, registry)
    assert Result.is_failure(result)

    fm.set_field(field, "")
    rule = RuleAllowFields(field=field)
    result = rule.validate(fm, registry)
    assert Result.is_failure(result)
