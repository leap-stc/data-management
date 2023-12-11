"""
...
"""
import xarray as xr
import apache_beam as beam
from pangeo_forge_recipes.patterns import pattern_from_file_sequence
from pangeo_forge_recipes.transforms import OpenURLWithFSSpec, OpenWithXarray, StoreToZarr

# Common Parameters
days = range(1, 32)
dataset_url = 'https://zenodo.org/records/10261274/files'

## Monthly version
input_urls = [f'{dataset_url}/eNATL60-BLBT02_y2009m07d{d:02d}.1d_TSW_60m.nc' for d in days]
pattern = pattern_from_file_sequence(input_urls, concat_dim='time')

def preprocess(ds:xr.Dataset) -> xr.Dataset:
    ds = ds.set_coords(['depthw', 'nav_lon', 'nav_lat'])
    return ds

pattern_monthly = pattern_from_file_sequence(input_urls, concat_dim='time_counter')
eNATL60_BLBT02 = (
    beam.Create(pattern.items())
    | OpenURLWithFSSpec()
    | OpenWithXarray(xarray_open_kwargs={'preprocess': preprocess})
    | StoreToZarr(
        store_name='eNATL60_BLBT02.zarr',
        combine_dims=pattern.combine_dim_keys,
    )
)