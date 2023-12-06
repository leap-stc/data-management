# This will be deleted before merge

from dataclasses import asdict, dataclass
from pathlib import Path

import requests
import yaml

API = 'https://api.pangeo-forge.org'
HERE = Path(__file__).parent


@dataclass
class Dataset:
    recipe_id: str
    dataset_url: str


@dataclass
class Store:
    name: str
    href: str


@dataclass
class Maintainer:
    name: str
    github_username: str


@dataclass
class Link:
    label: str
    href: str


@dataclass
class LEAPCatalogEntry:
    name: str
    description: str
    stores: list[Store]
    maintainers: list[Maintainer]
    links: list[Link]


if __name__ == '__main__':
    feedstocks = requests.get(API + '/feedstocks').json()
    datasets = {}
    for f in feedstocks:
        dss = requests.get(f"{API}/feedstocks/{f['id']}/datasets?type=production").json()
        if dss:  # not all feedstocks have datasets
            datasets.update(
                {f['spec']: [Dataset(ds['recipe_id'], ds['dataset_public_url']) for ds in dss]}
            )

    # these three feedstocks' datasets are unopenable, see:
    # https://github.com/pangeo-forge/pangeo-forge-orchestrator/issues/238#issuecomment-1841832249
    openable_datasets = {
        k: v
        for k, v in datasets.items()
        if k
        not in [
            'pangeo-forge/GPM_3IMERGDL-feedstock',
            'pangeo-forge/liveocean-feedstock',
            'pangeo-forge/aws-noaa-oisst-feedstock',
        ]
    }

    leap_catalog_entries: list[LEAPCatalogEntry] = []
    for feedstock, datasets in openable_datasets.items():
        meta_text = requests.get(
            f'https://raw.githubusercontent.com/{feedstock}/main/feedstock/meta.yaml'
        ).text
        meta_yaml = yaml.safe_load(meta_text)

        maintainers = [Maintainer(m['name'], m['github']) for m in meta_yaml['maintainers']]

        stores = []
        for ds in datasets:
            stores.append(Store(name=ds.recipe_id, href=ds.dataset_url))

        feedstock_link = Link(
            label='Pangeo Forge Feedstock',
            href=f'https://github.com/{feedstock}',
        )

        lce = LEAPCatalogEntry(
            name=meta_yaml['title'],
            description=meta_yaml['description'],
            stores=stores,
            maintainers=maintainers,
            links=[feedstock_link],
        )
        leap_catalog_entries.append(lce)

    for lce in leap_catalog_entries:
        fname = f"{lce.name.lower().replace(' ', '-')}.yaml"
        fname = fname.replace('(', '').replace(')', '')
        with open(HERE / 'datasets' / fname, mode='w') as f:
            yaml.dump(asdict(lce), f)
