import datetime as dt
import functools

import apache_beam as beam
import cftime
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

    start = cftime.datetime(year=1, month=2, day=1, minute=0, calendar='noleap')
    delta = dt.timedelta(minutes=20)
    # `range(210_240)` means the last value yielded is
    # `cftime.DatetimeNoLeap(9, 1, 31, 23, 40, 0, 0, has_year_zero=True)`
    for i in range(210_240):
        yield start + (delta * i)


def make_url(time: cftime.DatetimeNoLeap, ds_type: str):
    """Given a datetime and variable name, return a url pointing to the corresponding NetCDF file.

    For example, the inputs ``(cftime.DatetimeNoLeap(1, 2, 1, 0, 20, 0, 0, has_year_zero=True), "mli")`` will return:
    https://huggingface.co/datasets/LEAP/ClimSim_high-res/resolve/main/train/0001-02/E3SM-MMF.mli.0001-02-01-01200.nc
    """
    seconds = (time.hour * 3600) + (time.minute * 60)
    return (
        'https://huggingface.co/datasets/LEAP/ClimSim_high-res/resolve/main/train/'
        f'{time.year:04}-{time.month:02}/E3SM-MMF.{ds_type}.'
        f'{time.year:04}-{time.month:02}-{time.day:02}-{seconds:05}.nc'
    )


class ExpandTimeDimAndAddMetadata(beam.PTransform):
    """Preprocessor transform for ClimSim datasets."""

    @staticmethod
    def _preproc(item: Indexed[T]) -> Indexed[T]:
        """The preprocessor function, which is applied in `.expand` method of this class."""
        # import function-scope deps here (for beam serialization issue)
        import cftime
        import numpy as np

        index, ds = item

        ymd = str(ds.ymd.values)  # e.g., '10201'
        year = int(ymd[:-4])  # e.g., '10201'[:-4] -> '1'
        month = int(ymd[-4:-2])  # e.g., '10201'[-4:-2] -> '02'
        day = int(ymd[-2:])  # e.g., '10201'[-2:] -> '01'

        tod_as_minutes = int(ds.tod.values) // 60  # e.g., 37200 (sec) // 60 (sec/min) -> 620 min
        hour = tod_as_minutes // 60  # e.g., 620 min // 60 (min/hr) -> 10 hrs
        minute = tod_as_minutes % 60  # e.g., 620 min % 60 (min/hr) -> 20 min

        time = cftime.datetime(
            year=year,
            month=month,
            day=day,
            hour=hour,
            minute=minute,
            calendar='noleap',
        )
        ds = ds.expand_dims(time=np.array([time]))
        ds.time.encoding = {
            'units': 'minutes since 0001-02-01 00:00:00',
            'calendar': 'noleap',
        }
        variable_metadata = {
            # TODO: Add additional CF metadata, e.g. `standard_name`, to this dict.
            'pbuf_SOLIN': dict(long_name='Solar insolation', units='W/m2'),
            'pbuf_COSZRS': dict(long_name='Cosine of solar zenith angle', units=''),
            'pbuf_LHFLX': dict(long_name='Surface latent heat flux', units='W/m2'),
            'pbuf_SHFLX': dict(long_name='Surface sensible heat flux', units='W/m2'),
            'pbuf_TAUX': dict(long_name='Zonal surface stress', units='N/m2'),
            'pbuf_TAUY': dict(long_name='Meridional surface stress', units='N/m2'),
            'pbuf_ozone': dict(long_name='Ozone volume mixing ratio', units='mol/mol'),
            'pbuf_N2O': dict(long_name='N2O volume mixing ratio', units='mol/mol'),
            'pbuf_CH4': dict(long_name='CH4 volume mixing ratio', units='mol/mol'),
            'state_ps': dict(long_name='Surface pressure', units='Pa'),
            'state_q0001': dict(long_name='Specific humidity', units='kg/kg'),
            'state_q0002': dict(long_name='Cloud liquid mixing ratio', units='kg/kg'),
            'state_q0003': dict(long_name='Cloud ice mixing ratio', units='kg/kg'),
            'state_t': dict(long_name='Air temperature', units='K'),
            'state_u': dict(long_name='Zonal wind speed', units='m/s'),
            'state_v': dict(long_name='Meridional wind speed', units='m/s'),
            'state_pmid': dict(long_name='Mid-level pressure', units='Pa'),
            'cam_in_ASDIR': dict(long_name='Albedo for direct shortwave radiation', units=''),
            'cam_in_ASDIF': dict(long_name='Albedo for diffuse shortwave radiation', units=''),
            'cam_in_ALDIR': dict(long_name='Albedo for direct longwave radiation', units=''),
            'cam_in_ALDIF': dict(long_name='Albedo for diffuse longwave radiation', units=''),
            'cam_in_LWUP': dict(long_name='Upward longwave flux', units='W/m2'),
            'cam_in_SNOWHLAND': dict(
                long_name='Snow depth over land (liquid water equivalent)', units='m'
            ),
            'cam_in_SNOWHICE': dict(long_name='Snow depth over ice', units='m'),
            'cam_in_LANDFRAC': dict(long_name='Land areal fraction', units=''),
            'cam_in_ICEFRAC': dict(long_name='Sea-ice areal fraction', units=''),
            'cam_out_NETSW': dict(long_name='Net shortwave flux at surface', units='W/m2'),
            'cam_out_FLWDS': dict(long_name='Downward longwave flux at surface', units='W/m2'),
            'cam_out_PRECSC': dict(long_name='Snow rate (liquid water equivalent)', units='m/s'),
            'cam_out_PRECC': dict(long_name='Rain rate', units='m/s'),
            'cam_out_SOLS': dict(
                long_name='Downward visible direct solar flux to surface', units='W/m2'
            ),
            'cam_out_SOLL': dict(
                long_name='Downward near-infrared direct solar flux to surface', units='W/m2'
            ),
            'cam_out_SOLSD': dict(
                long_name='Downward visible diffuse solar flux to surface', units='W/m2'
            ),
            'cam_out_SOLLD': dict(
                long_name='Downward near-infrared diffuse solar flux to surface', units='W/m2'
            ),
        }
        for vname in variable_metadata:
            if vname in ds:
                ds[vname].attrs = variable_metadata[vname]

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
    | ExpandTimeDimAndAddMetadata()
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
