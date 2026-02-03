from typing import Annotated, Optional
from pydantic import BaseModel, ConfigDict, Field


class UpgradeArtifactResponse(BaseModel):
    model_config = ConfigDict(extra="allow")
    status: Annotated[
        int,
        Field(
            default=200,
            title="Status",
            description="Template Status: 200 for verified, or 422 for failed.",
        ),
    ] = 200
    requires_field_being: Annotated[
        bool,
        Field(
            title="Requires Field Being",
            description="Indicates if the upgraded template requires a field being to interact.",
        ),
    ]
    content: Annotated[
        str,
        Field(
            title="Template Content",
            description="Markdown contents containing Front-matter and body associated with the artifact to be upgraded.",
        ),
    ]
    artifact_name: Annotated[
        str,
        Field(
            title="Artifact Name",
            description="Artifact name such as, `Glyph of Silent Blessing`, associated with the upgraded template.",
        ),
    ]
    template_type: Annotated[
        str,
        Field(
            description="Type of the template, e.g., 'glyph', 'sigil', etc.",
            max_length=255,
        ),
    ]

    template_id: Annotated[
        str,
        Field(
            default="",
            title="Template ID",
            description="Unique identifier for the template.",
        ),
    ] = ""

    template_version: Annotated[
        str,
        Field(
            title="Template Type",
            description="Version of the template, e.g., '1.0', '2.10', etc.",
        ),
    ]

    upgraded_at: Annotated[
        str,
        Field(
            title="Upgraded At",
            description="Timestamp when the artifact was upgraded.",
        ),
    ]

    extra_fields: Annotated[
        list[str],
        Field(
            default_factory=list,
            title="Extra Fields",
            description="List of extra fields found not included in registry.",
        ),
    ]
    content_media_type: Annotated[
        Optional[str],
        Field(
            default="text/markdown",
            description="Media type (contentMediaType) of the content, default is 'text/markdown'.",
        ),
    ] = "text/markdown"
    content_has_front_matter: Annotated[
        Optional[bool],
        Field(
            default=True,
            description="Indicates if the content includes Front-Matter, default is True.",
        ),
    ] = True


class UpgradeArtifactMcpResponse(UpgradeArtifactResponse):
    pass

    @staticmethod
    def from_artifact_response(
        response: UpgradeArtifactResponse,
    ) -> "UpgradeArtifactMcpResponse":
        """
        Static Method: Creates an instance of UpgradeArtifactMcpResponse from an UpgradeArtifactResponse object.
        Args:
            response (UpgradeArtifactResponse): The original upgrade artifact response to convert.
        Returns:
            UpgradeArtifactMcpResponse: A new instance populated with data from the original response.
        """

        return UpgradeArtifactMcpResponse(**response.model_dump())


class UpgradeArtifactApiResponse(UpgradeArtifactResponse):
    template_api_path: Annotated[
        Optional[str],
        Field(
            default=None,
            title="Template API Path",
            description="API path for the template.",
        ),
    ] = None

    registry_api_path: Annotated[
        Optional[str],
        Field(
            default=None,
            title="Registry API Path",
            description="API path for the registry.",
        ),
    ] = None

    manifest_api_path: Annotated[
        Optional[str],
        Field(
            default=None,
            title="Manifest API Path",
            description="API path for the manifest.",
        ),
    ] = None

    instructions_api_path: Annotated[
        Optional[str],
        Field(
            default=None,
            title="Instructions API Path",
            description="API path for the instructions.",
        ),
    ] = None

    @staticmethod
    def from_artifact_response(
        response: UpgradeArtifactResponse,
    ) -> "UpgradeArtifactApiResponse":
        """
        Static Method: Creates an instance of UpgradeArtifactApiResponse from an UpgradeArtifactResponse object.
        Args:
            response (UpgradeArtifactResponse): The original upgrade artifact response to convert.
        Returns:
            UpgradeArtifactApiResponse: A new instance populated with data from the original response.
        """

        return UpgradeArtifactApiResponse(**response.model_dump())
