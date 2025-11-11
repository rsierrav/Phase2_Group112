"""
ECE 461 - Fall 2025 - Project Phase 2 - Group 112
"""

from fastapi import FastAPI
from fastapi.responses import RedirectResponse, Response
import yaml
from .routers import (
    artifacts,
    ingest,
    rating,
    cost,
    search,
    audit,
    lineage,
    license,
    auth,
    admin,
    tracks,
    health,
)

app = FastAPI(
    title="ECE 461 - Fall 2025 - Project Phase 2 - Group 112",
    version="3.4.4",
    description="API for ECE 461/Fall 2025/Project Phase 2 - Group 112",
    redirect_slashes=False,  # Disable automatic trailing slash redirects
)

# Include all routers
app.include_router(health.router)
app.include_router(auth.router)
app.include_router(admin.router)
app.include_router(artifacts.router)
app.include_router(ingest.router)
app.include_router(rating.router)
app.include_router(cost.router)
app.include_router(search.router)
app.include_router(audit.router)
app.include_router(lineage.router)
app.include_router(license.router)
app.include_router(tracks.router)

openapi_yaml: str | None = None


@app.get("/yaml", response_class=Response, include_in_schema=False)
def get_openapi_yaml():
    global openapi_yaml
    if openapi_yaml is None:
        openapi_spec = app.openapi()
        openapi_yaml = yaml.dump(openapi_spec, default_flow_style=False)

    return Response(content=openapi_yaml, media_type="application/yaml")


@app.get("/", include_in_schema=False)
async def root():
    """Redirect to API documentation."""
    return RedirectResponse(url="/docs")
