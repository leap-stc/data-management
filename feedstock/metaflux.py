"""
MetaFlux is a global, long-term carbon flux dataset of gross
primary production and ecosystem respiration that is generated
using meta-learning. This dataset will be added to the existing
rodeo forecast model in order to improve its performances."
"""
import apache_beam as beam
from pangeo_forge_recipes.patterns import pattern_from_file_sequence
from pangeo_forge_recipes.transforms import OpenURLWithFSSpec, OpenWithXarray, StoreToZarr

# Common Parameters
years = range(2001, 2022)
months = range(1, 13)
dataset_url = 'https://zenodo.org/record/7761881/files'

## Monthly version
input_urls_monthly = [f'{dataset_url}/METAFLUX_GPP_RECO_monthly_{y}.nc' for y in years]

pattern_monthly = pattern_from_file_sequence(input_urls_monthly, concat_dim='time')
METAFLUX_GPP_RECO_monthly = (
    beam.Create(pattern_monthly.items())
    | OpenURLWithFSSpec()  # open_kwargs=open_kwargs
    | OpenWithXarray()
    | StoreToZarr(
        store_name='METAFLUX_GPP_RECO_monthly.zarr',
        combine_dims=pattern_monthly.combine_dim_keys,
    )
)

## daily version
input_urls_daily = [
    f'{dataset_url}/METAFLUX_GPP_RECO_daily_{y}{m:02}.nc' for y in years for m in months
]
pattern_daily = pattern_from_file_sequence(input_urls_daily, concat_dim='time')
METAFLUX_GPP_RECO_daily = (
    beam.Create(pattern_daily.items())
    | OpenURLWithFSSpec()  # open_kwargs=open_kwargs
    | OpenWithXarray()
    | StoreToZarr(
        store_name='METAFLUX_GPP_RECO_daily.zarr',
        combine_dims=pattern_daily.combine_dim_keys,
    )
)
