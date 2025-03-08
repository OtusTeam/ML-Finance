import pathlib

from datasets import load_dataset
import pandas as pd
import typer


app = typer.Typer()

@app.command()
def download_data(
    dataset_name: str, 
    output_path: pathlib.Path
    ) -> None:
    output_path.mkdir(parents=True, exist_ok=True)
    
    print('Donwloading data...')
    hf_dataset = load_dataset(dataset_name)

    # В датасете может быть разное разбиение:
    # train-test, train-test-val, train
    # Поэтому проходимся итеративно по ключам
    for split_key in hf_dataset.keys():
        print(f'Saving {split_key} data...')
        pd.DataFrame(hf_dataset[split_key]).to_csv(
            f"{output_path}/{split_key}_dataset.csv", 
            index=False
            )

    print('Data downloading complete')

if __name__ == '__main__':
    app()
