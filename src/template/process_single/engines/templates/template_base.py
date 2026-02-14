from typing import Any
from pathlib import Path
from ....main_registry import MainRegistry
from .....config.pkg_config import PkgConfig
from ....front_mater_meta import FrontMatterMeta


class TemplateBase:
    def __init__(
        self,
        working_dir: Path,
        main_registry: MainRegistry,
        template_front_matter: FrontMatterMeta,
    ):
        self.__working_dir = working_dir
        self.__main_registry = main_registry
        self.__config = PkgConfig()
        self.__tci = self.config.templates_config_info.tci_items[
            template_front_matter.template_type
        ]
        self.__fm = self._get_filtered_front_matter(template_front_matter)

    def _get_filtered_front_matter(self, orig_fm: FrontMatterMeta) -> FrontMatterMeta:
        omitted_fields = self.tci.single_fields_omitted
        filtered_fm = {
            key: value
            for key, value in orig_fm.frontmatter.items()
            if key not in omitted_fields
        }

        fm = FrontMatterMeta.from_frontmatter_dict(
            file_path=orig_fm.file_path,
            fm_dict=filtered_fm,
            content=orig_fm.content,
        )
        return fm

    def _process_common(self, tokens: dict[str, Any]) -> None:
        self.fm.set_field(
            "template_registry",
            {
                "filename": f"{self.tci.template_type}-template-v{self.tci.template_version}-registry.yml",
                "registry_id": f"{self.tci.template_id}-V{self.tci.template_version}-REGISTRY",
                "enforced": True,
            },
        )

        self.fm.set_field(
            "canonical_prompt",
            {
                "required_invocation": True,
                "enforce_registry_match": True,
                "executor_file": f"{self.config.template_ceib_single.executor_mode}-V{self.config.template_ceib_single.version}.md",
                "executor_mode": f"{self.config.template_ceib_single.executor_mode}-V{self.config.template_ceib_single.version}",
            },
        )
        # the current role prompts are likely - "[[prompt:Choose from registry → metadata_fields → roles_authority → allowed_values]]"
        # for single, api, and mcp we want fields and not metadata_fields
        # this is because single, api and mcp use individual registry files.
        roles = (
            "roles_authority",
            "roles_visibility",
            "roles_function",
            "roles_action",
        )
        for role in roles:
            if self.fm.has_field(role):
                self.fm.set_field(
                    role,
                    [
                        f"[[prompt:Choose from registry → fields → {role} → allowed_values]]"
                    ],
                )
        # result["batch_number"] = str(self.main_registry.build_version)
        # self.fm.set_field("batch_number", str(self.main_registry.build_version))

    def _get_file_path(self) -> Path:
        return (
            self.working_dir
            / f"{self.fm.template_type}-template-v{self.fm.template_version}.md"
        )

    def _write_file(self) -> Path:
        output_path = self._get_file_path()
        self.fm.file_path = output_path
        self.fm.recompute_sha256()
        self.fm.write_template(output_path)
        # print(f"Generated registry file: {output_path.name}")
        return output_path

    @property
    def config(self) -> PkgConfig:
        return self.__config

    @property
    def main_registry(self) -> MainRegistry:
        return self.__main_registry

    @property
    def tci(self):
        return self.__tci

    @property
    def fm(self) -> FrontMatterMeta:
        return self.__fm

    @property
    def working_dir(self) -> Path:
        return self.__working_dir
