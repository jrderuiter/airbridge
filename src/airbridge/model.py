from typing import Any, Dict

from pydantic import BaseModel


class AirflowDatasetEvent(BaseModel):
    """Internal class used for separating dataset objects from the ORM."""

    dataset_uri: str
    extra: dict[str, Any]


class BridgeDatasetEvent(BaseModel):
    source_id: str
    dataset_uri: str
    extra: Dict[str, Any]
