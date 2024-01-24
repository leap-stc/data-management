"""
...
"""
import apache_beam as beam
from pangeo_forge_recipes.patterns import pattern_from_file_sequence
from pangeo_forge_recipes.transforms import (
    Indexed,
    OpenURLWithFSSpec,
    OpenWithXarray,
    StoreToZarr,
    T,
)

# Common Parameters
days = range(1, 32)
dataset_url = 'https://zenodo.org/records/10513552/files'

## Monthly version
input_urls = [f'{dataset_url}/eNATL60-BLBT02_y2009m07d{d:02d}.1d_TSWm_60m.nc' for d in days]
pattern = pattern_from_file_sequence(input_urls, concat_dim='time')


# does this succeed with all coords stripped?
class Preprocess(beam.PTransform):
    @staticmethod
    def _set_coords(item: Indexed[T]) -> Indexed[T]:
        index, ds = item
        ds = ds.set_coords(['deptht', 'depthw', 'nav_lon', 'nav_lat', 'time_counter', 'tmask'])
        ds = ds.assign_coords(
            tmask=ds.coords['tmask'].squeeze(), deptht=ds.coords['deptht'].squeeze()
        )
        return index, ds

    def expand(self, pcoll: beam.PCollection) -> beam.PCollection:
        return pcoll | 'Set coordinates' >> beam.Map(self._set_coords)


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
