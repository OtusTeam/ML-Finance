from datetime import datetime, timedelta
import os

from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator

# Функции для создания и удаления venv 
from my_utils.utils import create_new_venv, delete_venv


# Переменные, используемые в пайплайне
PROJECT_NAME = 'crypto_sentiment'
MLFLOW_HOST = "130.193.58.232"
MLFLOW_PORT = "5000"
MLFLOW_EXPERIMENT_NAME = "crypto_sentiment"

def run_create_new_venv_task() -> None:
    '''
    Обертка для функции создания venv
    '''
    create_new_venv(
        project_name=PROJECT_NAME,
        requirements_file='/opt/airflow/dags/scripts/requirements.txt'
        )

def run_delete_venv_task() -> None:
    '''
    Обертка для функции удаления venv
    '''
    delete_venv(project_name=PROJECT_NAME)

default_args = {
    'owner': 'airflow',
    'start_date': datetime(2025, 3, 5, 18, 20, 00),
    'retries': 1,
    'execution_timeout': timedelta(minutes=20)
}

dag = DAG(
    'crypto_sentiment_pipeline',
    default_args=default_args,
    description='A pipeline for train crypto sentiment model',
    schedule_interval='*/10 * * * *'
)

# Создание внутри контейнера с worker venv 
# и установка всех необходимых зависимостей
task_1 = PythonOperator(
    task_id='create_venv',
    python_callable=run_create_new_venv_task,
    dag=dag,
)

# Пайплайн, аналогичный пайплайну в dvc.yaml
task_2 = BashOperator(
    task_id='download_data',
    bash_command=f'/opt/airflow/.venv_{PROJECT_NAME}/bin/python3 ' 
                f'/opt/airflow/dags/scripts/src/data/get_data.py ' 
                f'flowfree/crypto-news-headlines ' 
                f'/opt/airflow/scripts/data/raw ',
    dag=dag,
)

task_3 = BashOperator(
    task_id='generate_embeddings',
    bash_command=f'/opt/airflow/.venv_{PROJECT_NAME}/bin/python3 ' 
                f'/opt/airflow/dags/scripts/src/features/generate_features.py ' 
                f'cointegrated/LaBSE-en-ru ' 
                f'/opt/airflow/scripts/data/raw ' 
                f'text ' 
                f'/opt/airflow/scripts/data/processed ',
    dag=dag,
)

task_4 = BashOperator(
    task_id='train_model',
    bash_command=f'/opt/airflow/.venv_{PROJECT_NAME}/bin/python3 '
                f'/opt/airflow/dags/scripts/src/models/train.py '
                f'/opt/airflow/scripts/data/processed/train_dataset.csv '
                f'label '
                f'l1 '
                f'/opt/airflow/scripts/models '
                f'{MLFLOW_HOST} '
                f'{MLFLOW_PORT} '
                f'{MLFLOW_EXPERIMENT_NAME} '
                f'/opt/airflow/scripts/reports',
    dag=dag,
)

task_5 = BashOperator(
    task_id='evaluate_model',
    bash_command=f'/opt/airflow/.venv_{PROJECT_NAME}/bin/python3 '
                f'/opt/airflow/dags/scripts/src/models/evaluate.py '
                f'/opt/airflow/scripts/models/crypto_sentiment_clf.joblib '
                f'/opt/airflow/scripts/data/processed/test_dataset.csv '
                f'label '
                f'/opt/airflow/scripts/reports '
                f'{MLFLOW_HOST} '
                f'{MLFLOW_PORT} '
                f'{MLFLOW_EXPERIMENT_NAME}',
    dag=dag,
)

task_6 = BashOperator(
    task_id='compare_models',
    bash_command=f'/opt/airflow/.venv_{PROJECT_NAME}/bin/python3 '
                f'/opt/airflow/dags/scripts/src/models/compare.py '
                f'/opt/airflow/scripts/data/processed/validation_dataset.csv '
                f'label '
                f'/opt/airflow/scripts/models/crypto_sentiment_clf.joblib '
                f'/opt/airflow/scripts/reports',
    dag=dag,
)

task_7 = BashOperator(
    task_id='push_to_s3',
    bash_command=f'/opt/airflow/.venv_{PROJECT_NAME}/bin/python3 '
                f'/opt/airflow/dags/scripts/src/models/push.py '
                f'/opt/airflow/scripts/models/crypto_sentiment_clf.joblib '
                f'/opt/airflow/scripts/reports',
    dag=dag,
)

# Удаляем venv внутри worker
task_8 = PythonOperator(
    task_id='delete_venv',
    python_callable=run_delete_venv_task,
    dag=dag,
)

task_1 >> task_2 >> task_3 >> task_4 >> task_5 >> task_6 >> task_7 >> task_8
