import pendulum
from airflow import DAG
from airflow.datasets import Dataset
from airflow.operators.python import PythonOperator

input_dataset = Dataset("local://team_b/dataset_1")

with DAG(
    dag_id="process_data_from_team_b",
    schedule=[input_dataset],
    start_date=pendulum.yesterday(tz="UTC"),
):
    PythonOperator(
        task_id="hello_world",
        python_callable=lambda: print("Hello world!"),
    )
