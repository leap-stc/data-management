"""
Wave Watch 3
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

years = range(1993, 2023)
months = range(1, 13)
dates = []
for y in years:
    for m in months:
        dates.append((y, m))


def make_full_path(date: tuple[int, int]):
    year, month = date
    return f'https://data-dataref.ifremer.fr/ww3/GLOBMULTI_ERA5_GLOBCUR_01/GLOB-30M/{year}/FIELD_NC/LOPS_WW3-GLOB-30M_{year}{month:02d}.nc'


input_urls = [make_full_path(date) for date in dates]
pattern = pattern_from_file_sequence(input_urls, concat_dim='time')


# does this succeed with all coords stripped?
class StripCoords(beam.PTransform):
    @staticmethod
    def _strip_all_coords(item: Indexed[T]) -> Indexed[T]:
        """
        Many netcdfs contain variables other than the one specified in the `variable_id` facet.
        Set them all to coords
        """
        index, ds = item
        print(f'Preprocessing before {ds =}')
        ds = ds.reset_coords(drop=True)
        print(f'Preprocessing after {ds =}')
        return index, ds

    def expand(self, pcoll: beam.PCollection) -> beam.PCollection:
        return pcoll | 'Debug: Remove coordinates' >> beam.Map(self._strip_all_coords)


WW3 = (
    beam.Create(pattern.items())
    | OpenURLWithFSSpec()
    | OpenWithXarray(xarray_open_kwargs={'preprocess':lambda ds: ds.set_coords('MAPSTA')})
    | StripCoords()
    | StoreToZarr(
        store_name='WW3.zarr',
        combine_dims=pattern.combine_dim_keys,
        target_chunks={'time': 200},
    )
)
