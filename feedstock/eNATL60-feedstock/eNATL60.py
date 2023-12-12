"""
...
"""
import apache_beam as beam
import xarray as xr
from pangeo_forge_recipes.patterns import pattern_from_file_sequence
from pangeo_forge_recipes.transforms import OpenURLWithFSSpec, OpenWithXarray, StoreToZarr, Indexed, T

# Common Parameters
days = range(1, 32)
dataset_url = 'https://zenodo.org/records/10261274/files'

## Monthly version
input_urls = [f'{dataset_url}/eNATL60-BLBT02_y2009m07d{d:02d}.1d_TSW_60m.nc' for d in days]
pattern = pattern_from_file_sequence(input_urls, concat_dim='time')

# does this succeed with all coords stripped?
class Preprocess(beam.PTransform):
    @staticmethod
    def _set_coords(item: Indexed[T]) -> Indexed[T]:
        index, ds = item
        ds.set_coords(['depthw', 'nav_lon', 'nav_lat'])
        return index, ds

    def expand(self, pcoll: beam.PCollection) -> beam.PCollection:
        return pcoll | 'Set coordinates' >> beam.Map(self._set_coords)

pattern_monthly = pattern_from_file_sequence(input_urls, concat_dim='time_counter')
eNATL60_BLBT02 = (
    beam.Create(pattern.items())
    | OpenURLWithFSSpec()
    | OpenWithXarray()
    | Preprocess()
    | StoreToZarr(
        store_name='eNATL60_BLBT02.zarr',
        combine_dims=pattern.combine_dim_keys,
    )
)
