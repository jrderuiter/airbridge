from airflow import DAG
from airflow.datasets import Dataset
from airflow.operators.python import PythonOperator
import pendulum


input_dataset = Dataset("my_favorite_dataset")


with DAG(
    dag_id="example_consumer",
    schedule=[input_dataset],
    start_date=pendulum.yesterday(tz="UTC")
):
    PythonOperator(
        task_id="hello_world",
        python_callable=lambda: print("Hello world!"),
    )
