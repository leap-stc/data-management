import os

import aiohttp
import apache_beam as beam
from pangeo_forge_recipes.patterns import pattern_from_file_sequence
from pangeo_forge_recipes.transforms import OpenURLWithFSSpec, OpenWithXarray, StoreToZarr

username, password = os.environ['EARTHDATA_USERNAME'], os.environ['EARTHDATA_PASSWORD']
client_kwargs = {
    'auth': aiohttp.BasicAuth(username, password),
    'trust_env': True,
}

# the urls are a bit hard to construct, so lets try with a few hardcoded ones
input_urls = [
    'https://ladsweb.modaps.eosdis.nasa.gov/archive/allData/62/MCD06COSP_M3_MODIS/2023/182/MCD06COSP_M3_MODIS.A2023182.062.2023223000656.nc',
    'https://ladsweb.modaps.eosdis.nasa.gov/archive/allData/62/MCD06COSP_M3_MODIS/2023/213/MCD06COSP_M3_MODIS.A2023213.062.2023254000930.nc',
    'https://ladsweb.modaps.eosdis.nasa.gov/archive/allData/62/MCD06COSP_M3_MODIS/2023/244/MCD06COSP_M3_MODIS.A2023244.062.2023285000449.nc',
]

# ? the files have no time coordinate, so we need to construct it?
# For now just try to concat along a non-coordinate dimension

pattern = pattern_from_file_sequence(input_urls, concat_dim='time')

MODIS_COSP = (
    beam.Create(pattern.items())
    | OpenURLWithFSSpec(
        open_kwargs={'block_size': 0, 'client_kwargs': client_kwargs},
        max_concurrency=10,
    )
    | OpenWithXarray()
    | StoreToZarr(
        target_chunks={'time': 3},
        store_name='MODIS_COSP.zarr',
        combine_dims=pattern.combine_dim_keys,
    )
)
