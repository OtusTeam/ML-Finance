import json
import pathlib
from pprint import pprint

import mlflow
import joblib
import pandas as pd
from sklearn.metrics import precision_score, recall_score
import typer


app = typer.Typer()


@app.command()
def evaluate_model(
    model_path: pathlib.Path,
    dataset_path: str,
    target_column_name: str,
    reports_path: pathlib.Path,
    mlflow_host: str,
    mlflow_port: str,
    mlflow_experiment_name: str
    ) -> None:
    reports_path.mkdir(parents=True, exist_ok=True)

    mlflow.set_tracking_uri(f'http://{mlflow_host}:{mlflow_port}')
    mlflow.set_experiment(mlflow_experiment_name)

    with open(reports_path / 'mlflow_current_run_id.json', 'r') as f:
        mlflow_run_id = json.load(f)

    # Загружаем run_id, который был в train.py
    with mlflow.start_run(
        run_id=mlflow_run_id, 
        log_system_metrics=True
        ) as run:
        print(f'Loading model {model_path}...')
        model = joblib.load(model_path)

        print(f'Loading test dataset {dataset_path}...')
        dataset = pd.read_csv(dataset_path)
        X_test = [json.loads(one_example) for one_example in dataset['embeds'].to_list()]
        y_test = dataset[target_column_name]

        print('Evaluating model...')
        y_pred = model.predict(X_test)

        scores = {
            'recall_micro': float(recall_score(y_test, y_pred, average='micro')),
            'recall_macro': float(recall_score(y_test, y_pred, average='macro')),
            'recall_weighted': float(recall_score(y_test, y_pred, average='weighted')),
            'precision_micro': float(precision_score(y_test, y_pred, average='micro')),
            'precision_macro': float(precision_score(y_test, y_pred, average='macro')),
            'precision_weighted': float(precision_score(y_test, y_pred, average='weighted'))
            }
        mlflow.log_metrics(scores)
        

        print('Generating report...')
        with open(reports_path / 'test_metrics.json', 'w') as f:
            json.dump(scores, f)
        print(f'Report saved to {reports_path}')

        pprint(scores)

        print('Evaluating complete')

if __name__ == '__main__':
    app()
