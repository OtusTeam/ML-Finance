import json
import pathlib

import joblib
import mlflow
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
import typer
import sys

if __name__ == "__main__" and __package__ is None:
    sys.path.append(str(pathlib.Path(__file__).resolve().parents[2]))

from src.settings import LOGGER


app = typer.Typer()


@app.command()
def train_model(
        train_dataset_path: pathlib.Path,
        target_column_name: str,
        penalty: str,
        output_path: pathlib.Path,
        mlflow_host: str,
        mlflow_port: str,
        mlflow_experiment_name: str,
        reports_path: pathlib.Path
) -> None:
    output_path.mkdir(parents=True, exist_ok=True)
    reports_path.mkdir(parents=True, exist_ok=True)

    mlflow.set_tracking_uri(f'http://{mlflow_host}:{mlflow_port}')
    mlflow.set_experiment(mlflow_experiment_name)

    with mlflow.start_run(log_system_metrics=True) as run:
        mlflow.log_param('penalty', penalty)

        LOGGER.info(f'Reading {train_dataset_path}')
        training_data = pd.read_csv(train_dataset_path)

        LOGGER.info('Preparing data for training...')
        y = training_data[target_column_name]
        X = np.array(
            [json.loads(one_example) for one_example in training_data['embeds'].to_list()]
        )

        LOGGER.info('Training model...')
        classifier = LogisticRegression(penalty=penalty, solver='saga')

        classifier.fit(X, y)

        LOGGER.info('Saving model...')
        joblib.dump(classifier, f'{output_path}/crypto_sentiment_clf.joblib')

        LOGGER.info('Pushing model to MLFlow server...')
        mlflow.sklearn.log_model(
            sk_model=classifier,
            artifact_path="logreg",
            input_example=X[:1]
        )

        # Если процесс обучения разбит на части, то можно получить run_id
        # текущего запуска эксперимента и потом его подставить в другом скрипте
        # В таком случае всё продолжит логироваться в тот же запуск
        with open(reports_path / 'mlflow_current_run_id.json', 'w') as f:
            json.dump(run.info.run_id, f)

        LOGGER.info('Training complete')


if __name__ == '__main__':
    app()