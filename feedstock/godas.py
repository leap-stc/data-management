"""
NCEP Global Ocean Data Assimilation System (GODAS)
"""
import apache_beam as beam
from pangeo_forge_recipes.patterns import MergeDim, FilePattern
from pangeo_forge_recipes.transforms import OpenURLWithFSSpec, OpenWithXarray, StoreToZarr

variables = ['sshg', 'thflx'] 

def make_full_path(variable):
    return f'https://downloads.psl.noaa.gov/Datasets/godas/Derived/{var}.mon.ltm.nc'
variable_merge_dim = MergeDim("variable", variables)

pattern = FilePattern(make_full_path, variable_merge_dim)

GODAS = (
    beam.Create(pattern.items())
    | OpenURLWithFSSpec()
    | OpenWithXarray()
    | StoreToZarr(
        target_chunks={'time':10},
        store_name="GODAS.zarr",
        combine_dims=pattern.combine_dim_keys,
    )
)