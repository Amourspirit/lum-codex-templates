from pathlib import Path
from ....front_mater_meta import FrontMatterMeta

class MapTypeName:
    def __init__(self, templates: list[Path]) -> None:
        """
        Maps template types to their file paths.

        Args:
            templates (list[Path]): A list of template file paths.
        """
        self.templates = templates
    
    def map(self) -> dict[str, str]:
        """
        Build a mapping from template type names to template file paths.
        Return a dictionary where each key is the value of a template's front-matter
        "template_type" field and the value is the template's file path (as provided in
        self.templates).
        
        Only templates that contain a "template_type" front-matter field are included.
        If multiple templates share the same "template_type", the last one encountered
        overwrites earlier entries (i.e., "last-one-wins"). The function does not
        mutate any templates or external state.
        
        Returns:
            dict[str, str]: Mapping of template_type -> template_path.
        
        Raises:
            Any exceptions propagated from FrontMatterMeta when a template file cannot
            be read or its front matter cannot be parsed.
        
        Notes:
            - The method assumes self.templates is an iterable of file path strings.
            - The returned keys are expected to be strings (as indicated by the return
            type), though the front-matter value will be used as-is.
            - Complexity is O(n) with respect to the number of templates, plus the
            cost of parsing each template's front matter.
        """
        
        type_name_map = {}
        for template_path in self.templates:
            fm = FrontMatterMeta(template_path)
            if fm.has_field("template_type"):
                type_name_map[fm.template_type] = template_path
        return type_name_map