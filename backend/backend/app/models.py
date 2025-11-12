"""Pydantic models for all API schemas."""

from enum import Enum
from typing import Annotated, Any, Literal, Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field, HttpUrl, StringConstraints


# Basic Types
class ArtifactType(str, Enum):
    """Artifact category."""

    model = "model"
    dataset = "dataset"
    code = "code"


# Unique identifier for the artifact - must contain only alphanumeric characters and hyphens
ArtifactID = Annotated[
    str,
    StringConstraints(pattern=r"^[a-zA-Z0-9\-]+$"),
    Field(
        description="Unique identifier for use with artifact endpoints.", examples=["48472749248"]
    ),
]

ArtifactName = str
AuthenticationToken = str
EnumerateOffset = str
ActionType = Literal["CREATE", "UPDATE", "DOWNLOAD", "RATE", "AUDIT"]


# User Models
class User(BaseModel):
    """User information."""

    name: str = Field(description="Username", examples=["Alfalfa"])
    is_admin: bool = Field(description="Is this user an admin?", examples=[True])


class UserAuthenticationInfo(BaseModel):
    """Authentication info for a user."""

    password: str = Field(
        description="Password for a user",
        examples=["correcthorsebatterystaple123(!__+@**(A'\";DROP TABLE artifacts;"],
    )


class AuthenticationRequest(BaseModel):
    """Authentication request payload."""

    user: User
    secret: UserAuthenticationInfo


# Artifact Models
class ArtifactData(BaseModel):
    """Source location for ingesting an artifact.

    Provide a single downloadable url pointing to a bundle that contains the artifact assets.
    """

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "url": "https://huggingface.co/openai/whisper-tiny/tree/main",
                "download_url": "https://ec2-10-121-34-12/download/whisper-tiny",
            }
        }
    )
    url: HttpUrl = Field(description="Artifact source url used during ingest.")
    download_url: Optional[HttpUrl] = Field(
        None,
        description="Direct download link served by your server for retrieving the stored artifact bundle. Present only in responses.",
    )


class ArtifactMetadata(BaseModel):
    """The `name` is provided when uploading an artifact.

    The `id` is used as an internal identifier for interacting with existing artifacts and distinguishes artifacts that share a name.
    """

    name: ArtifactName = Field(description="Name of the artifact", examples=["audience-classifier"])
    id: ArtifactID
    type: ArtifactType = Field(description="Type of artifact", examples=["model"])


class Artifact(BaseModel):
    """Artifact envelope containing metadata and ingest details."""

    metadata: ArtifactMetadata
    data: ArtifactData


class ArtifactQuery(BaseModel):
    """Query parameters for searching artifacts."""

    name: ArtifactName = Field(description="Name of artifact to query")
    types: Optional[list[ArtifactType]] = Field(
        None, description="Optional list of artifact types to filter results"
    )


class ArtifactRegEx(BaseModel):
    """Regular expression query for artifacts."""

    regex: str = Field(description="A regular expression over artifact names and READMEs")


# Audit Models
class ArtifactAuditEntry(BaseModel):
    """One entry in an artifact's audit history."""

    user: User
    date: datetime = Field(
        description="Date of activity using ISO-8601 Datetime standard in UTC format.",
        examples=["2023-03-23 23:11:15+00:00"],
    )
    artifact: ArtifactMetadata
    action: ActionType


# Lineage Models
class ArtifactLineageNode(BaseModel):
    """A single node in an artifact lineage graph."""

    artifact_id: ArtifactID = Field(description="Unique identifier for the node")
    name: str = Field(
        description="Human-readable label for the node.", examples=["audience-classifier"]
    )
    source: str = Field(
        description="Provenance for how the node was discovered.", examples=["config_json"]
    )
    metadata: Optional[dict[str, Any]] = Field(
        None, description="Optional metadata captured for lineage analysis."
    )


class ArtifactLineageEdge(BaseModel):
    """Directed relationship between two lineage nodes."""

    from_node_artifact_id: ArtifactID = Field(description="Identifier of the upstream node")
    to_node_artifact_id: ArtifactID = Field(description="Identifier of the downstream node")
    relationship: str = Field(
        description="Qualitative description of the edge.", examples=["fine_tuning_dataset"]
    )


class ArtifactLineageGraph(BaseModel):
    """Complete lineage graph for an artifact."""

    nodes: list[ArtifactLineageNode] = Field(
        description="Nodes participating in the lineage graph."
    )
    edges: list[ArtifactLineageEdge] = Field(
        description="Directed edges describing lineage relationships"
    )


# License Check Models
class SimpleLicenseCheckRequest(BaseModel):
    """Request payload for artifact license compatibility analysis."""

    github_url: HttpUrl = Field(description="GitHub repository url to evaluate")


# Rating Models
class SizeScore(BaseModel):
    """Size suitability scores for common deployment targets."""

    raspberry_pi: float = Field(description="Size score for Raspberry Pi class devices")
    jetson_nano: float = Field(description="Size score for Jetson Nano deployments")
    desktop_pc: float = Field(description="Size score for desktop deployments")
    aws_server: float = Field(description="Size score for cloud server deployments")


class ModelRating(BaseModel):
    """Model rating summary generated by the evaluation service."""

    name: str = Field(description="Human-friendly label for the evaluated model")
    category: str = Field(description="Model category assigned during evaluation")
    net_score: float = Field(description="Overall score synthesizing all metrics")
    net_score_latency: float = Field(description="Time (seconds) required to compute net_score")
    ramp_up_time: float = Field(description="Ease-of-adoption rating for the model")
    ramp_up_time_latency: float = Field(
        description="Time (seconds) required to compute ramp_up_time"
    )
    bus_factor: float = Field(description="Team redundancy score for the upstream project")
    bus_factor_latency: float = Field(description="Time (seconds) required to compute bus_factor")
    performance_claims: float = Field(
        description="Alignment between stated and observed performance"
    )
    performance_claims_latency: float = Field(
        description="Time (seconds) required to compute performance_claims"
    )
    license: float = Field(description="Licensing suitability score")
    license_latency: float = Field(description="Time (seconds) required to compute license")
    dataset_and_code_score: float = Field(
        description="Availability and quality of accompanying datasets and code"
    )
    dataset_and_code_score_latency: float = Field(
        description="Time (seconds) required to compute dataset_and_code_score"
    )
    dataset_quality: float = Field(description="Quality rating for associated datasets")
    dataset_quality_latency: float = Field(
        description="Time (seconds) required to compute dataset_quality"
    )
    code_quality: float = Field(description="Quality rating for provided code artifacts")
    code_quality_latency: float = Field(
        description="Time (seconds) required to compute code_quality"
    )
    reproducibility: float = Field(description="Likelihood that reported results can be reproduced")
    reproducibility_latency: float = Field(
        description="Time (seconds) required to compute reproducibility"
    )
    reviewedness: float = Field(description="Measure of peer or community review coverage")
    reviewedness_latency: float = Field(
        description="Time (seconds) required to compute reviewedness"
    )
    tree_score: float = Field(description="Supply-chain health score for model dependencies")
    tree_score_latency: float = Field(description="Time (seconds) required to compute tree_score")
    size_score: SizeScore = Field(
        description="Size suitability scores for common deployment targets"
    )
    size_score_latency: float = Field(description="Time (seconds) required to compute size_score")


# Cost Models
class ArtifactCostDetail(BaseModel):
    """Cost details for a single artifact."""

    standalone_cost: Optional[float] = Field(
        None, description="The standalone cost of this artifact excluding dependencies"
    )
    total_cost: float = Field(description="The total cost of the artifact")


ArtifactCost = dict[ArtifactID, ArtifactCostDetail]


# Tracks Model
class TracksResponse(BaseModel):
    """Response containing planned implementation tracks."""

    plannedTracks: list[str] = Field(description="List of tracks the student plans to implement")


# Health Models
HealthStatus = Literal["ok", "degraded", "critical", "unknown"]
HealthMetricValue = int | float | str | bool


class HealthRequestSummary(BaseModel):
    """Request activity observed within the health window."""

    window_start: datetime = Field(description="Beginning of the aggregation window (UTC)")
    window_end: datetime = Field(description="End of the aggregation window (UTC)")
    total_requests: Optional[int] = Field(
        None, description="Number of API requests served during the window", ge=0
    )
    per_route: Optional[dict[str, int]] = Field(
        None, description="Request counts grouped by API route"
    )
    per_artifact_type: Optional[dict[str, int]] = Field(
        None, description="Request counts grouped by artifact type (model/dataset/code)"
    )
    unique_clients: Optional[int] = Field(
        None, description="Distinct API clients observed in the window", ge=0
    )


class HealthComponentBrief(BaseModel):
    """Lightweight component-level status summary."""

    id: str = Field(description="Stable identifier for the component")
    display_name: Optional[str] = Field(None, description="Human readable component name")
    status: HealthStatus
    issue_count: Optional[int] = Field(
        None, description="Number of outstanding issues contributing to the status", ge=0
    )
    last_event_at: Optional[datetime] = Field(
        None, description="Last significant event timestamp for the component"
    )


class HealthLogReference(BaseModel):
    """Link or descriptor for logs relevant to a health component."""

    label: str = Field(description="Human readable log descriptor")
    url: HttpUrl = Field(description="Direct link to download or tail the referenced log")
    tail_available: Optional[bool] = Field(
        None, description="Indicates whether streaming tail access is supported"
    )
    last_updated_at: Optional[datetime] = Field(
        None, description="Timestamp of the latest log entry available for this reference"
    )


class HealthSummaryResponse(BaseModel):
    """High-level snapshot summarizing registry health and recent activity."""

    status: HealthStatus
    checked_at: datetime = Field(
        description="Timestamp when the health snapshot was generated (UTC)"
    )
    window_minutes: int = Field(
        description="Size of the trailing observation window in minutes", ge=5
    )
    uptime_seconds: Optional[int] = Field(
        None, description="Seconds the registry API has been running", ge=0
    )
    version: Optional[str] = Field(
        None, description="Running service version or git SHA when available"
    )
    request_summary: Optional[HealthRequestSummary] = None
    components: Optional[list[HealthComponentBrief]] = Field(
        None, description="Rollup of component status ordered by severity"
    )
    logs: Optional[list[HealthLogReference]] = Field(
        None, description="Quick links or descriptors for recent log files"
    )


class HealthTimelineEntry(BaseModel):
    """Time-series datapoint for a component metric."""

    bucket: datetime = Field(description="Start timestamp of the sampled bucket (UTC)")
    value: float = Field(description="Observed value for the bucket")
    unit: Optional[str] = Field(None, description="Unit associated with the metric value")


class HealthIssue(BaseModel):
    """Outstanding issue or alert impacting a component."""

    code: str = Field(description="Machine readable issue identifier")
    severity: Literal["info", "warning", "error"] = Field(description="Issue severity")
    summary: str = Field(description="Short description of the issue")
    details: Optional[str] = Field(
        None, description="Extended diagnostic detail and suggested remediation"
    )


class HealthComponentDetail(BaseModel):
    """Detailed status, metrics, and log references for a component."""

    id: str = Field(description="Stable identifier for the component")
    display_name: Optional[str] = Field(None, description="Human readable component name")
    status: HealthStatus
    observed_at: datetime = Field(
        description="Timestamp when data for this component was last collected (UTC)"
    )
    description: Optional[str] = Field(
        None, description="Overview of the component's responsibility"
    )
    metrics: Optional[dict[str, Any]] = Field(
        None, description="Arbitrary metric key/value pairs describing component performance"
    )
    issues: Optional[list[HealthIssue]] = None
    timeline: Optional[list[HealthTimelineEntry]] = None
    logs: Optional[list[HealthLogReference]] = None


class HealthComponentCollection(BaseModel):
    """Detailed health diagnostics broken down per component."""

    components: list[HealthComponentDetail]
    generated_at: datetime = Field(
        description="Timestamp when the component report was created (UTC)"
    )
    window_minutes: Optional[int] = Field(
        None, description="Observation window applied to the component metrics", ge=5
    )
