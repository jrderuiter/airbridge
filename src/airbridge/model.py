from typing import Dict, Any
from pydantic import BaseModel


class BridgeDatasetEvent(BaseModel):
    source: str
    dataset_uri: str
    extra: Dict[str, Any]
