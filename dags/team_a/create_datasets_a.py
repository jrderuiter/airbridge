import pendulum
from airflow import DAG
from airflow.datasets import Dataset
from airflow.operators.python import PythonOperator

from airbridge.operators import emit_events

output_dataset_1 = Dataset("local://team_a/dataset_1")
output_dataset_2 = Dataset("local://team_a/dataset_2")


with DAG(
    dag_id="create_datasets_a",
    schedule=None,
    start_date=pendulum.yesterday(tz="UTC"),
) as dag:
    create_dataset_1 = PythonOperator(
        task_id="create_dataset_1",
        python_callable=lambda: print("Hello world!"),
        outlets=[output_dataset_1],
    )

    create_dataset_2 = PythonOperator(
        task_id="create_dataset_2",
        python_callable=lambda: print("Hello world!"),
        outlets=[output_dataset_2],
    )

    # emit_events = EmitEventOperator(task_id="emit_events", conn_id="test")
    # [create_dataset_1, create_dataset_2] >> emit_events

    emit_events(dag=dag, task_id="emit_events", conn_id="airbridge_broker")
