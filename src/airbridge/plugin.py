from airflow.plugins_manager import AirflowPlugin

from .listeners import DatasetListeners


class AirbridgePlugin(AirflowPlugin):
    name = "airflow_airbridge"
    listeners = [DatasetListeners()]
