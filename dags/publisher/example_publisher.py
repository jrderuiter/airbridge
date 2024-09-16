from airflow import DAG
from airflow.datasets import Dataset
from airflow.operators.python import PythonOperator
import pendulum


output_dataset = Dataset("my_favorite_dataset")


with DAG(
    dag_id="example_publisher",
    schedule=None,
    start_date=pendulum.yesterday(tz="UTC")
):
    PythonOperator(
        task_id="hello_world",
        python_callable=lambda: print("Hello world!"),
        outlets=[output_dataset]
    )
