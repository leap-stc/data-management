"""
NCEP Global Ocean Data Assimilation System (GODAS)
"""
import apache_beam as beam
from pangeo_forge_recipes.patterns import MergeDim, ConcatDim, FilePattern
from pangeo_forge_recipes.transforms import OpenURLWithFSSpec, OpenWithXarray, StoreToZarr

variables = ['sshg', 'thflx'] 
years = [1980, 1981, 1982]

def make_full_path(variable, year):
    return f"'https://downloads.psl.noaa.gov/Datasets/godas/{variable}.{year}.nc'"
    return f'https://downloads.psl.noaa.gov/Datasets/godas/Derived/{variable}.mon.ltm.nc'
variable_merge_dim = MergeDim("variable", variables)
time_concat_dim = ConcatDim("time", years)


pattern = FilePattern(make_full_path, variable_merge_dim, time_concat_dim)

GODAS = (
    beam.Create(pattern.items())
    | OpenURLWithFSSpec()
    | OpenWithXarray()
    | StoreToZarr(
        target_chunks={'time':120},
        store_name="GODAS.zarr",
        combine_dims=pattern.combine_dim_keys,
    )
)