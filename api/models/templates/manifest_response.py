from typing import Annotated, Optional
from pydantic import BaseModel, Field


class CanonicalMode(BaseModel):
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


class ManifestResponse(BaseModel):
    registry_file: Annotated[
        str,
        Field(
            title="Registry File",
            description="Name of the registry file associated with the template. E.g., `registry.json`.",
        ),
    ]
    template_file: Annotated[
        str,
        Field(
            title="Template File",
            description="Name of the template file associated with the template. E.g., `template.md`.",
        ),
    ]
    template_type: Annotated[
        str,
        Field(
            title="Template Type",
            description="Type of the template. E.g., `glyph`.",
        ),
    ]
    template_hash_algorithm: Annotated[
        str,
        Field(
            title="Template Hash Algorithm",
            description="Hash algorithm used for the template. E.g., `sha256`.",
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
    registry_id: Annotated[
        str,
        Field(
            title="Registry ID",
            description="Unique identifier for the registry.",
        ),
    ]

    canonical_mode: Annotated[
        CanonicalMode,
        Field(
            title="Canonical Mode",
            description="Information about the canonical executor mode for this template.",
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
    installed_at: Annotated[
        str,
        Field(
            title="Installed At",
            description="The date and time when the template was installed.",
        ),
    ]
    instructions_file: Annotated[
        str,
        Field(
            title="Instructions File",
            description="Name of the instructions file for the template. E.g., `instructions.md`.",
        ),
    ]
    template_id: Annotated[
        str,
        Field(
            title="Template ID",
            description="Unique identifier for the template.",
        ),
    ]

    # Optional fields that may be added dynamically by the API
    template_api_path: Annotated[
        Optional[str],
        Field(
            title="Template API Path",
            description="The API path to retrieve the template content.",
        ),
    ] = None
    instructions_api_path: Annotated[
        Optional[str],
        Field(
            title="Instructions API Path",
            description="The API path to retrieve the template instructions.",
        ),
    ] = None
    registry_api_path: Annotated[
        Optional[str],
        Field(
            title="Registry API Path",
            description="The API path to retrieve the template registry.",
        ),
    ] = None
    manifest_api_path: Annotated[
        Optional[str],
        Field(
            title="Manifest API Path",
            description="The API path to retrieve the template manifest.",
        ),
    ] = None
    executor_mode_api_path: Annotated[
        Optional[str],
        Field(
            title="Executor Mode API Path",
            description="The API path to retrieve the executor mode information.",
        ),
    ] = None
