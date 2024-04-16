import json
import traceback

import pydantic_core
import upath
import yaml
from schema import Feedstock, convert_to_raw_github_url


class ValidationError(Exception):
    def __init__(self, errors: list[dict[str, str]] | str) -> None:
        self.errors = errors
        super().__init__(self.errors)


def collect_feedstocks(path: upath.UPath) -> list[upath.UPath]:
    """Collects all the datasets in the given directory."""

    url = convert_to_raw_github_url(path)
    if feedstocks := yaml.safe_load(upath.UPath(url).read_text())['feedstocks']:
        print(feedstocks)
        return feedstocks
    else:
        # raise no json files found
        raise FileNotFoundError(f'No YAML files (.yaml or .yml) found in {path}')


def validate_feedstocks(*, feedstocks: upath.UPath) -> list[Feedstock]:
    def format_report(title: str, feedstocks: list[dict], include_traceback: bool = False) -> str:
        report = f'{title} ({len(feedstocks)})\n'
        if not feedstocks:
            report += '  🚀 None found\n'
        else:
            for entry in feedstocks:
                report += f"  📂 {entry['feedstock']}\n"
                if include_traceback:
                    report += f"    🔎 {entry['traceback']}\n"
        return report

    errors = []
    valid = []
    catalog = []

    for feedstock in feedstocks:
        try:
            feed = Feedstock.from_yaml(convert_to_raw_github_url(feedstock))
            valid.append({'feedstock': str(feedstock), 'status': 'valid'})
            catalog.append(feed)
        except Exception:
            errors.append({'feedstock': str(feedstock), 'traceback': traceback.format_exc()})

    valid_report = format_report('✅ Valid feedstocks:', valid)
    invalid_report = format_report('❌ Invalid feedstocks:', errors, include_traceback=True)

    print(valid_report)
    print(invalid_report)
    print('\n\n')

    if errors:
        raise ValidationError('Validation failed')

    return catalog


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('--path', type=str, help='Path to the feedstocks directory', required=True)
    args = parser.parse_args()
    feedstocks = collect_feedstocks(args.path)
    catalog = validate_feedstocks(feedstocks=feedstocks)
    here = upath.UPath(__file__).parent.resolve()

    # write catalog to JSON file for use in the website
    with open(f'{here}/output/consolidated-web-catalog.json', 'w') as f:
        json.dump(catalog, f, indent=2, default=pydantic_core.to_jsonable_python)
