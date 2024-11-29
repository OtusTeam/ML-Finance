import json
import pathlib
import tempfile

import boto3
import joblib
import pandas as pd
from sklearn.metrics import precision_score, recall_score
import typer


app = typer.Typer()


@app.command()
def compare_models(
    eval_dataset_path: pathlib.Path, 
    target_column_name: str,
    new_model_path: pathlib.Path,
    reports_path: pathlib.Path
    ) -> None:
    print('Loading new model...')
    new_model = joblib.load(new_model_path)

    print('Loading old model...')
    s3_session = boto3.session.Session()
    s3_client = s3_session.client(
        service_name='s3',
        endpoint_url='https://storage.yandexcloud.net'
    )
    
    with tempfile.TemporaryFile() as fp:
        fp.write(s3_client.get_object(
            Bucket='otus-test-bucket',
            Key='crypto_sentimnet_clf/crypto_sentiment_clf.joblib'
            )['Body'].read())
        fp.seek(0)
        old_model = joblib.load(fp)

    print(f'Loading eval dataset {eval_dataset_path}...')
    dataset = pd.read_csv(eval_dataset_path)
    X_val = [json.loads(one_example) for one_example in dataset['embeds'].to_list()]
    y_val = dataset[target_column_name]

    print('Evaluating models...')
    y_pred_new = new_model.predict(X_val)
    y_pred_old = old_model.predict(X_val)


    is_recall_micro_new_better = float(recall_score(y_val, y_pred_new, average='micro')) > \
        float(recall_score(y_val, y_pred_old, average='micro'))
    is_recall_macro_new_better = float(recall_score(y_val, y_pred_new, average='macro')) > \
        float(recall_score(y_val, y_pred_old, average='macro'))
    is_recall_weighted_new_better = float(recall_score(y_val, y_pred_new, average='weighted')) > \
        float(recall_score(y_val, y_pred_old, average='weighted'))
    is_precision_micro_new_better = float(precision_score(y_val, y_pred_new, average='micro')) > \
        float(precision_score(y_val, y_pred_old, average='micro'))
    is_precision_macro_new_better = float(precision_score(y_val, y_pred_new, average='macro')) > \
        float(precision_score(y_val, y_pred_old, average='macro'))
    is_precision_weighted_new_better = float(precision_score(y_val, y_pred_new, average='weighted')) > \
        float(precision_score(y_val, y_pred_old, average='weighted'))
    
    if all([
            is_recall_micro_new_better, 
            is_recall_macro_new_better, 
            is_recall_weighted_new_better,
            is_precision_micro_new_better,
            is_precision_macro_new_better,
            is_precision_weighted_new_better
        ]):
        print('New model is better!')
        with open(f'{reports_path}/best_model.json', 'w') as f:
            json.dump({'best_model': 'new'}, f)
    else:
        print('Old model is better (')
        with open(f'{reports_path}/best_model.json', 'w') as f:
            json.dump({'best_model': 'old'}, f)


if __name__ == '__main__':
    app()
