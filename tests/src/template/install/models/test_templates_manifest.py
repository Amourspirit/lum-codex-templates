import pytest

if __name__ == "__main__":
    pytest.main([__file__])

from src.template.single.install.models.templates_manifest import (
    TemplateEntry,
    TemplatesManifest,
)


def test_template_entry_creation():
    """Test creating a TemplateEntry instance."""
    entry = TemplateEntry(
        name="Test Template", type="glyph", versions=["1.0.0", "1.1.0", "2.0.0"]
    )
    assert entry.name == "Test Template"
    assert entry.type == "glyph"
    assert entry.versions == ["1.0.0", "1.1.0", "2.0.0"]


def test_templates_manifest_creation():
    """Test creating a TemplatesManifest instance."""
    templates = {
        "glyph": TemplateEntry(
            name="Glyph Template", type="glyph", versions=["1.0.0", "2.0.0"]
        ),
        "dyad": TemplateEntry(
            name="Dyad Template", type="dyad", versions=["1.1.0", "1.0.0"]
        ),
    }
    manifest = TemplatesManifest(templates=templates)
    assert len(manifest.templates) == 2
    assert "glyph" in manifest.templates
    assert "dyad" in manifest.templates
    assert manifest.templates["glyph"].name == "Glyph Template"
    assert manifest.templates["dyad"].type == "dyad"


def test_get_sorted_templates():
    """Test that get_sorted_templates sorts templates by name and versions descending."""
    templates = {
        "dyad": TemplateEntry(
            name="Dyad Template", type="dyad", versions=["1.0.0", "2.0.0", "1.1.0"]
        ),
        "glyph": TemplateEntry(
            name="Glyph Template", type="glyph", versions=["1.0.0", "1.2.0"]
        ),
    }
    manifest = TemplatesManifest(templates=templates)
    sorted_manifest = manifest.get_sorted_templates()

    # Templates should be sorted by name: "Dyad Template" before "Glyph Template"
    # Assuming keys are "dyad" and "glyph", and dict preserves insertion order after sorting
    keys = list(sorted_manifest.templates.keys())
    assert keys == ["dyad", "glyph"]

    # Versions for "dyad" should be sorted descending: ["2.0.0", "1.1.0", "1.0.0"]
    assert sorted_manifest.templates["dyad"].versions == ["2.0.0", "1.1.0", "1.0.0"]

    # Versions for "glyph" should be sorted descending: ["1.2.0", "1.0.0"]
    assert sorted_manifest.templates["glyph"].versions == ["1.2.0", "1.0.0"]

    # Ensure other fields are preserved
    assert sorted_manifest.templates["dyad"].name == "Dyad Template"
    assert sorted_manifest.templates["dyad"].type == "dyad"
    assert sorted_manifest.templates["glyph"].name == "Glyph Template"
    assert sorted_manifest.templates["glyph"].type == "glyph"


def test_get_sorted_templates_empty():
    """Test get_sorted_templates with an empty manifest."""
    manifest = TemplatesManifest(templates={})
    sorted_manifest = manifest.get_sorted_templates()
    assert sorted_manifest.templates == {}


def test_get_sorted_templates_single_entry():
    """Test get_sorted_templates with a single template entry."""
    templates = {
        "seal": TemplateEntry(
            name="Seal Template", type="seal", versions=["3.0.0", "1.0.0", "2.0.0"]
        )
    }
    manifest = TemplatesManifest(templates=templates)
    sorted_manifest = manifest.get_sorted_templates()
    assert list(sorted_manifest.templates.keys()) == ["seal"]
    assert sorted_manifest.templates["seal"].versions == ["3.0.0", "2.0.0", "1.0.0"]
