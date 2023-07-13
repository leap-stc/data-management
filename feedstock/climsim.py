import apache_beam as beam
from pangeo_forge_recipes.patterns import
from pangeo_forge_recipes.transforms import OpenURLWithFSSpec, OpenWithXarray, StoreToZarr

# TODO:
days_per_month = {1:31, 2:28, 3:31, 4:30, 5:31, 6:30, 7:31, 8:31, 9:30, 10:31, 11:30, 12:31}
var_names = ['mli']
month_and_day =

def make_url(year, month_and_day, sample, var_name):
    month = month_and_day.split('_')[0]
    # example https://huggingface.co/datasets/LEAP/ClimSim_high-res/resolve/main/train/0001-02/E3SM-MMF.mli.0001-02-01-00000.nc
    f"https://huggingface.co/datasets/LEAP/ClimSim_high-res/resolve/main/train/{year:04i}-{month:02}/E3SM-MMF.mli.{year:04i}-{month_and_day}-{sample}.nc



pattern = pattern_from_file_sequence(input_urls, concat_dim='sample')


CASM = (
    beam.Create(pattern.items())
    | OpenURLWithFSSpec()
    | OpenWithXarray()
    | StoreToZarr(
        target_chunks={'date': 20},
        store_name='ClimSim_high-res_train.zarr',
        combine_dims=pattern.combine_dim_keys,
    )
)
