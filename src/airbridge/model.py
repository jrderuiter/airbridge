from typing import Any, Dict

from pydantic import BaseModel


class AirflowDatasetEvent(BaseModel):
    """Internal class used for separating dataset objects from the ORM."""

    dataset_uri: str
    extra: dict[str, Any]

    @classmethod
    def from_json(cls, body: bytes) -> "AirflowDatasetEvent":
        return cls.model_validate_json(body)


class AirbridgeDatasetEvent(BaseModel):
    """Data model used on the broker."""

    source_id: str
    dataset_uri: str
    extra: Dict[str, Any]

    @classmethod
    def from_json(cls, body: bytes) -> "AirbridgeDatasetEvent":
        return cls.model_validate_json(body)
