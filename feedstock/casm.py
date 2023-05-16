"""
TODO: Add docstring
"""
import apache_beam as beam
from pangeo_forge_recipes.patterns import pattern_from_file_sequence
from pangeo_forge_recipes.transforms import OpenURLWithFSSpec, OpenWithXarray, StoreToZarr


#years = range(2002, 2021)
years = range(2012, 2021) # for debugging

input_urls = [
    f"https://zenodo.org/record/7072512/files/CASM_SM_{year}.nc" for year in years]

pattern = pattern_from_file_sequence(input_urls, concat_dim='date')
CASM = (
    beam.Create(pattern.items())
    | OpenURLWithFSSpec()
    | OpenWithXarray()
    | StoreToZarr(
        store_name="CASM.zarr",
        combine_dims=pattern.combine_dim_keys,
    )
)
