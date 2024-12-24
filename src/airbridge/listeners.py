# import asyncio

# from airflow.models.dataset import DatasetEvent

# from .clients.rabbitmq import RmqPublisher
# from .config import get_settings
# from .model import BridgeDatasetEvent


# class DatasetListeners:
#     pass
#     # @hookimpl
#     # def on_dataset_changed(
#     #     self, dataset: Dataset,
#     # ):
#     #     print(f"DATASET CHANGED: {dataset}")
#     #     # if dataset.extra["from_rest_api"]:
#     #     #     print("Forwarding event")
#     #     #     _publish_event(dataset=dataset)
#     #     # else:
#     #     #     print("Not forwarding event from API")

#     # @hookimpl
#     # def on_dataset_event_created(
#     #     self, event: DatasetEvent,
#     # ):
#     #     print(f"DATASET EVENT CREATED: {event}")
#     #     if not event.extra.get("from_rest_api", False):
#     #         print("Publishing event to bridge")
#     #         _publish(event)
#     #     else:
#     #         print("Not publishing API event from API")


# # def _is_from_api(dataset)


# def _publish(event: DatasetEvent):
#     settings = get_settings()

#     publisher = RmqPublisher(
#         host=settings.broker.host,
#         exchange_name=settings.broker.exchange,
#         login=settings.broker.login,
#         password=settings.broker.password,
#     )

#     bridge_event = BridgeDatasetEvent(
#         source=settings.general.instance_id,
#         dataset_uri=event.dataset.uri,
#         extra=event.extra
#     )

#     asyncio.run(publisher.publish(bridge_event.model_dump_json().encode()))
