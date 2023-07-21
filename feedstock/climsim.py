import datetime as dt
import functools

import apache_beam as beam
from pangeo_forge_recipes.patterns import ConcatDim, FilePattern
from pangeo_forge_recipes.transforms import (
    Indexed,
    OpenURLWithFSSpec,
    OpenWithXarray,
    StoreToZarr,
    T,
)


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


def make_url(time: dt.datetime, ds_type: str):
    """Given a datetime and variable name, return a url pointing to the corresponding NetCDF file.

    For example, the inputs ``(dt.datetime(1, 2, 1, 0, 20), "mli")`` will return:
    https://huggingface.co/datasets/LEAP/ClimSim_high-res/resolve/main/train/0001-02/E3SM-MMF.mli.0001-02-01-01200.nc
    """
    seconds = (time.hour * 3600) + (time.minute * 60)
    return (
        'https://huggingface.co/datasets/LEAP/ClimSim_high-res/resolve/main/train/'
        f'{time.year:04}-{time.month:02}/E3SM-MMF.{ds_type}.'
        f'{time.year:04}-{time.month:02}-{time.day:02}-{seconds:05}.nc'
    )


class ExpandTimeDimAndRenameVars(beam.PTransform):
    """ """

    @staticmethod
    def _preproc(item: Indexed[T]) -> Indexed[T]:
        """"""
        index, ds = item

        ymd = str(ds.ymd.values)  # e.g., '10201'
        year, month, day = int(ymd[:-4]), int(ymd[-4:-2]), int(ymd[-2:])
        minute = int(ds.tod.values)
        time = dt.datetime(year=year, month=month, day=day, minute=minute)
        ds = ds.expand_dims(time=[time])
        # FIXME: Drop ymd + tod vars now that time dimension is added?
        # FIXME: Don't rename vars. Add metadata to vars below instead.
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


OpenAndPreprocess = (
    OpenURLWithFSSpec()
    | OpenWithXarray(
        # FIXME: Get files to open without `copy_to_local=True`
        # Related: what is the filetype? Looks like netcdf3, but for some reason
        # `scipy` backend can't open them, and `netcdf4` can?
        copy_to_local=True,
        xarray_open_kwargs=dict(engine='netcdf4'),
    )
    | ExpandTimeDimAndRenameVars()
)

times = [t for t in generate_times()]
concat_dim = ConcatDim('time', keys=times)

mli_make_url = functools.partial(make_url, ds_type='mli')
mli_pattern = FilePattern(mli_make_url, concat_dim)
climsim_highres_mli = (
    beam.Create(mli_pattern.items())
    | OpenAndPreprocess
    | StoreToZarr(
        store_name='climsim-highres-mli.zarr',
        target_chunks={'time': 20},
        combine_dims=mli_pattern.combine_dim_keys,
    )
)

mlo_make_url = functools.partial(make_url, ds_type='mlo')
mlo_pattern = FilePattern(mlo_make_url, concat_dim)
climsim_highres_mlo = (
    beam.Create(mlo_pattern.items())
    | OpenAndPreprocess
    | StoreToZarr(
        store_name='climsim-highres-mlo.zarr',
        target_chunks={'time': 20},
        combine_dims=mlo_pattern.combine_dim_keys,
    )
)
