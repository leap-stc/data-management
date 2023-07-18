import apache_beam as beam
import pandas as pd
from pangeo_forge_recipes.patterns import ConcatDim, FilePattern, MergeDim
from pangeo_forge_recipes.transforms import OpenURLWithFSSpec, OpenWithXarray, StoreToZarr

var_names = ['mli', 'mlo']
times = pd.date_range('0001-02-01', '0009-02-01', freq='1200S', unit='s', inclusive='left')


def make_url(t: pd.Timestamp, var_name: str):
    """Given a timestamp and variable name, return a url pointing to the corresponding NetCDF file.

    For example, the inputs ``(pd.Timestamp("0001-02-01 00:20:00"), "mli")`` will return:
    https://huggingface.co/datasets/LEAP/ClimSim_high-res/resolve/main/train/0001-02/E3SM-MMF.mli.0001-02-01-01200.nc
    """
    seconds = (t.hour * 3600) + (t.minute * 60)
    return (
        'https://huggingface.co/datasets/LEAP/ClimSim_high-res/resolve/main/train/'
        f'{t.year:04}-{t.month:02}/E3SM-MMF.{var_name}.'
        f'{t.year:04}-{t.month:02}-{t.day:02}-{seconds:05}.nc'
    )


concat_dim = ConcatDim('t', keys=times)
merge_dim = MergeDim('var', keys=var_names)
pattern = FilePattern(make_url, concat_dim, merge_dim)

climsim = (
    beam.Create(pattern.items())
    | OpenURLWithFSSpec()
    | OpenWithXarray()
    | StoreToZarr(
        target_chunks={'time': 20},
        store_name='climsim-highres-train.zarr',
        combine_dims=pattern.combine_dim_keys,
    )
)
