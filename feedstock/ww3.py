"""
Wave Watch 3
"""
import apache_beam as beam
from pangeo_forge_recipes.patterns import pattern_from_file_sequence
from pangeo_forge_recipes.transforms import OpenURLWithFSSpec, OpenWithXarray, StoreToZarr

years = range(2020, 2023)
months = range(1, 13)
dates = []
for y in years:
    for m in months:
        dates.append((y, m))


def make_full_path(date: tuple[int, int]):
    year, month = date
    return f"https://data-dataref.ifremer.fr/ww3/GLOBMULTI_ERA5_GLOBCUR_01/GLOB-30M/{year}/FIELD_NC/LOPS_WW3-GLOB-30M_{year}{month:02d}.nc"


input_urls = [make_full_path(date) for date in dates]
pattern = pattern_from_file_sequence(input_urls, concat_dim='time')

WW3 = (
    beam.Create(pattern.items())
    | OpenURLWithFSSpec()
    | OpenWithXarray()
    | StoreToZarr(
        store_name='WW3.zarr',
        combine_dims=pattern.combine_dim_keys,
    )
)
