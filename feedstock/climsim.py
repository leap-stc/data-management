import datetime as dt

import apache_beam as beam
from pangeo_forge_recipes.patterns import ConcatDim, FilePattern, MergeDim
from pangeo_forge_recipes.transforms import (
    Indexed,
    OpenURLWithFSSpec,
    OpenWithXarray,
    StoreToZarr,
    T,
)

var_names = ['mli', 'mlo']


def generate_times():
    """Generate datetimes for the range covered by the ClimSim dataset."""

    # Note that an arguably simpler way to generate the same datetimes yielded by this generator
    # would be to use pandas as follows:
    # ```
    # pd.date_range('0001-02-01', '0009-02-01', freq='1200S', unit='s', inclusive='left')
    # ```
    # We are not doing that here because, in order to get dates starting from the year 1, we need
    # to pass the ``unit='s'`` option, however this option was added in `pandas==2.0.0`, which is
    # not yet supported in Beam: https://github.com/apache/beam/issues/27221.

    start = dt.datetime(year=1, month=2, day=1, minute=0)
    delta = dt.timedelta(minutes=20)
    # FIXME: calendar is noleap, remove extra feb day from leap year
    for i in range(210_384):  # means the last value yielded is `dt.datetime(9, 1, 31, 23, 40)`
        yield start + (delta * i)


def make_url(time: dt.datetime, var: str):
    """Given a datetime and variable name, return a url pointing to the corresponding NetCDF file.

    For example, the inputs ``(dt.datetime(1, 2, 1, 0, 20), "mli")`` will return:
    https://huggingface.co/datasets/LEAP/ClimSim_high-res/resolve/main/train/0001-02/E3SM-MMF.mli.0001-02-01-01200.nc
    """
    seconds = (time.hour * 3600) + (time.minute * 60)
    return (
        'https://huggingface.co/datasets/LEAP/ClimSim_high-res/resolve/main/train/'
        f'{time.year:04}-{time.month:02}/E3SM-MMF.{var}.'
        f'{time.year:04}-{time.month:02}-{time.day:02}-{seconds:05}.nc'
    )


times = [t for t in generate_times()]

concat_dim = ConcatDim('time', keys=times)
merge_dim = MergeDim('var', keys=var_names)
pattern = FilePattern(make_url, concat_dim, merge_dim)


class ExpandTimeDimAndRenameVars(beam.PTransform):
    """ """

    @staticmethod
    def _preproc(item: Indexed[T]) -> Indexed[T]:
        """"""
        index, ds = item

        # FIXME: what's a better format to parse this into?
        timestamp = str(ds.ymd.values) + str(ds.tod.values)

        ds = ds.expand_dims(time=[timestamp])

        overlapping = [
            'ymd',
            'tod',
            'state_q0001',
            'state_q0002',
            'state_q0003',
            'state_t',
            'state_u',
            'state_v',
        ]
        ds_type = 'mli' if 'cam_in_ALDIF' in ds.data_vars else 'mlo'
        rename = {vname: f'{ds_type}_{vname}' for vname in overlapping}
        ds = ds.rename(rename)
        return index, ds

    def expand(self, pcoll: beam.PCollection) -> beam.PCollection:
        return pcoll | beam.Map(self._preproc)


climsim_highres = (
    beam.Create(pattern.items())
    | OpenURLWithFSSpec()
    | OpenWithXarray(
        # FIXME: Get files to open without `copy_to_local=True`
        # Related: what is the filetype? Looks like netcdf3, but for some reason
        # `scipy` backend can't open them, and `netcdf4` can?
        copy_to_local=True,
        xarray_open_kwargs=dict(engine='netcdf4'),
    )
    | ExpandTimeDimAndRenameVars()
    | StoreToZarr(
        target_chunks={'time': 20},
        store_name='climsim-highres-train.zarr',
        combine_dims=pattern.combine_dim_keys,
    )
)
