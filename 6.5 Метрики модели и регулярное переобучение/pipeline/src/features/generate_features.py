import pathlib

import pandas as pd
import torch
from transformers import AutoTokenizer, AutoModel
import typer


app = typer.Typer()


@app.command()
def create_embeddings(
    model_name: str, 
    dataset_path: pathlib.Path,
    target_column_name: str,
    output_path: pathlib.Path
    ) -> None:
    output_path.mkdir(parents=True, exist_ok=True)

    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModel.from_pretrained(model_name)

    for one_dataset_file in pathlib.Path(dataset_path).glob('*.csv'):
        filename = one_dataset_file.name
        print(f'Processing {filename}...')
        dataset = pd.read_csv(one_dataset_file)

        sentences = dataset[target_column_name].to_list()

        print(f'Tokenizing {filename}...')
        encoded_input = tokenizer(
            sentences, 
            padding=True,
            truncation=True, 
            max_length=64, 
            return_tensors='pt'
            )

        print(f'Generating embeddings for {filename}...')
        with torch.no_grad():
            model_output = model(**encoded_input)

        embeddings = model_output.pooler_output
        embeddings = torch.nn.functional.normalize(embeddings)

        dataset['embeds'] = embeddings.cpu().numpy().tolist()

        print(f'Saving result to {output_path}/{filename}...')
        dataset.to_csv(f'{output_path}/{filename}')
    print('Embeddings generation complete')

if __name__ == '__main__':
    app()
