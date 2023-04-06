import traceback

import upath
from schema import Dataset


class ValidationError(Exception):
    def __init__(self, errors: list[dict[str, str]]) -> None:
        self.errors = errors
        super().__init__(self.errors)


def collect_datasets(path: str) -> list[upath.UPath]:
    """Collects all the datasets in the given directory."""
    path = upath.UPath(path).resolve()
    if not path.exists():
        # raise path does not exist
        raise FileNotFoundError(f'{path} directory does not exist')

    if not path.is_dir():
        # raise path is not a directory
        raise NotADirectoryError(f'{path} is not a directory')

    if datasets := sorted(path.glob('*.json')):
        return datasets
    else:
        # raise no json files found
        raise FileNotFoundError(f'No json files found in {path}')


def validate_datasets(datasets: upath.UPath) -> None:
    def format_report(title: str, datasets: list[dict], include_traceback: bool = False) -> str:
        report = f'{title} ({len(datasets)})\n'
        if not datasets:
            report += '  🚀 None found\n'
        else:
            for dataset in datasets:
                report += f"  📂 {dataset['dataset']}\n"
                if include_traceback:
                    report += f"    🔎 {dataset['traceback']}\n"
        return report

    errors = []
    valid = []

    for dataset in datasets:
        try:
            Dataset.parse_file(dataset)
            valid.append({'dataset': str(dataset), 'status': 'valid'})
        except Exception:
            errors.append({'dataset': str(dataset), 'traceback': traceback.format_exc()})

    valid_report = format_report('✅ Valid datasets:', valid)
    invalid_report = format_report('❌ Invalid datasets:', errors, include_traceback=True)

    print(valid_report)
    print(invalid_report)
    print('\n\n')

    if errors:
        raise ValidationError(errors)


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('--path', type=str, help='Path to the datasets directory', required=True)
    args = parser.parse_args()
    datasets = collect_datasets(args.path)
    validate_datasets(datasets)
