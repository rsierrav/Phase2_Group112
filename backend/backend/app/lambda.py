from typing import Any
from mangum import Mangum
from mangum.handlers import APIGateway
from mangum.types import Scope, LambdaEvent, LambdaContext, LambdaConfig

from .main import app


# From https://github.com/Kludex/mangum/issues/147#issuecomment-1833920783
class APIGatewayCorrectedRootPath(APIGateway):
    """A variant of the APIGateway Mangum handler which guesses the root path.

    The `root_path` property of the ASGI scope is intended to indicate a
    subpath the API is served from. This handler will try to guess this
    prefix based on the difference between the requested path and the
    resource path API gateway reports.

    Using this should eleviate the need to manually specify the root path in
    FastAPI.
    """

    @staticmethod
    def _find_root_path(event: LambdaEvent) -> str:
        # This is the full path, including /<stage> at the start
        request_path = event.get("requestContext", {}).get("path", "")
        # This is the path of the resource, not including a prefix
        resource_path = event.get("path", "")
        root_path = ""
        if request_path.endswith(resource_path):
            root_path = request_path[: -len(resource_path)]

        return root_path

    def __init__(
        self, event: LambdaEvent, context: LambdaContext, config: LambdaConfig, *_args: Any
    ) -> None:
        super().__init__(event, context, config)

    @property
    def scope(self) -> Scope:
        return {**super().scope, "root_path": self._find_root_path(self.event)}


handler = Mangum(app, custom_handlers=[APIGatewayCorrectedRootPath])
