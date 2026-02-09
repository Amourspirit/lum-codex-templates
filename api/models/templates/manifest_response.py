from typing import Annotated
from pydantic import BaseModel, ConfigDict, Field


class TemplateInfo(BaseModel):
    model_config = ConfigDict(extra="allow")
    template_type: Annotated[
        str,
        Field(
            title="Template Type",
            description="Type of the template.",
        ),
    ]

    template_file: Annotated[
        str,
        Field(
            title="Template File",
            description="Name of the template file associated with the template. E.g., `template.md`.",
        ),
    ]
    version: Annotated[
        str,
        Field(
            title="Template Version",
            description="Version of the template. E.g., `v1.0`.",
        ),
    ]
    hash: Annotated[
        str,
        Field(
            title="Template Hash",
            description="Hash value of the template entire file.",
        ),
    ]
    template_hash: Annotated[
        str,
        Field(
            title="Template Hash",
            description="Hash value of the template file, excluding the templates front-matter `template_hash` field.",
        ),
    ]
    template_hash_algorithm: Annotated[
        str,
        Field(
            title="Template Hash Algorithm",
            description="Hash algorithm used for the template. E.g., `sha256`.",
        ),
    ]
    status: Annotated[
        str,
        Field(
            title="Status",
            description="Current status of the template. E.g., `available`.",
        ),
    ]
    requires_field_being: Annotated[
        bool,
        Field(
            title="Requires Field Being",
            description="Indicates if the template requires a field being for execution.",
        ),
    ]

    template_id: Annotated[
        str,
        Field(
            title="Template ID",
            description="Unique identifier for the template.",
        ),
    ]


class RegistryInfo(BaseModel):
    model_config = ConfigDict(extra="allow")
    registry_id: Annotated[
        str,
        Field(
            title="Registry ID",
            description="Unique identifier for the registry.",
        ),
    ]
    registry_file: Annotated[
        str,
        Field(
            title="Registry File",
            description="Name of the registry file associated with the template. E.g., `registry.json`.",
        ),
    ]


class InstructionsInfo(BaseModel):
    model_config = ConfigDict(extra="allow")
    instructions_file: Annotated[
        str,
        Field(
            title="Instructions File",
            description="Name of the instructions file for the template. E.g., `instructions.md`.",
        ),
    ]


class CanonicalMode(BaseModel):
    model_config = ConfigDict(extra="allow")
    version: Annotated[
        str,
        Field(
            title="Executor Mode Version",
            description="The version of the executor mode used by the template.",
        ),
    ]
    executor_mode: Annotated[
        str,
        Field(
            title="Executor Mode",
            description="The name of the executor mode used by the template.",
        ),
    ]


class ManifestMcpResponse(BaseModel):
    model_config = ConfigDict(extra="allow")
    name: Annotated[
        str,
        Field(
            title="Manifest Name",
            description="Name of the manifest.",
        ),
    ]
    version: Annotated[
        str,
        Field(
            title="Manifest Version",
            description="Version of the manifest.",
        ),
    ]
    description: Annotated[
        str,
        Field(
            title="Manifest Description",
            description="Description of the manifest.",
        ),
    ]
    template_info: Annotated[
        TemplateInfo,
        Field(
            title="Template Information",
            description="Information about the template associated with the manifest.",
        ),
    ]
    registry_info: Annotated[
        RegistryInfo,
        Field(
            title="Registry Information",
            description="Information about the registry associated with the template.",
        ),
    ]
    instructions_info: Annotated[
        InstructionsInfo,
        Field(
            title="Instructions Information",
            description="Information about the instructions associated with the template.",
        ),
    ]
    installed_at: Annotated[
        str,
        Field(
            title="Installed At",
            description="Timestamp indicating when the template was installed.",
        ),
    ]

    canonical_mode: Annotated[
        CanonicalMode,
        Field(
            title="Canonical Mode",
            description="Information about the canonical executor mode for this template.",
        ),
    ]

    @staticmethod
    def from_manifest_response(
        manifest_response: "ManifestResponse",
    ) -> "ManifestMcpResponse":
        """Converts a ManifestResponse to a ManifestMcpResponse."""
        return ManifestMcpResponse.model_validate(manifest_response.model_dump())


class ManifestResponse(ManifestMcpResponse):
    model_config = ConfigDict(extra="allow")
