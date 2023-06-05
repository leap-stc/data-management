import glob
import json
from datetime import datetime

import gcsfs
import xarray as xr
from dask.diagnostics import ProgressBar

## Group file lists
# Total dataset: 10 years
# Train subset:  8 years
# Test subset:   2 years
# (Each suset has separate files for input and output.)

datadir = '/ocean/projects/atm200007p/sungduk/LEAP/E3SM_MMF_dataset/preprocess/hugging/E3SM-MMF_ne4'
FLIST = {}
FLIST['train'] = {}
for k in ['input', 'output']:
    f_train_1 = glob.glob(f'{datadir}/train/{k}/*.0001-0[23456789].nc')
    f_train_2 = glob.glob(f'{datadir}/train/{k}/*.0001-1[012].nc')
    f_train_3 = glob.glob(f'{datadir}/train/{k}/*.000[2345678]-*.nc')
    f_train_4 = glob.glob(f'{datadir}/train/{k}/*.0009-01.nc')
    FLIST['train'][k] = sorted([*f_train_1, *f_train_2, *f_train_3, *f_train_4])
FLIST['test'] = {}
for k in ['input', 'output']:
    f_test_1 = glob.glob(f'{datadir}/test/{k}/*.0009-0[3456789].nc')
    f_test_2 = glob.glob(f'{datadir}/test/{k}/*.0009-1[012].nc')
    f_test_3 = glob.glob(f'{datadir}/test/{k}/*.0010-*.nc')
    f_test_4 = glob.glob(f'{datadir}/test/{k}/*.0011-0[12].nc')
    FLIST['test'][k] = sorted([*f_test_1, *f_test_2, *f_test_3, *f_test_4])


## Turn to a mf dataset
def postprocess(ds):
    if 'pbuf_00060' in ds.dims:
        ds = ds.rename({'pbuf_00060': 'lev'})
    ds = ds.chunk({'sample': 72 * 21})  # 3 weeks per chunk
    return ds


def main(flist):
    ds = xr.open_mfdataset(
        flist, concat_dim='sample', combine='nested', parallel=True
    )  # ,preprocess=_preprocess
    ds = postprocess(ds)
    return ds


DS = {}
for j in ['train', 'test']:
    DS[j] = {}
    for k in ['input', 'output']:
        print(j, k)
        print('start: ', datetime.now())
        flist = FLIST[j][k]
        DS[j][k] = main(flist)
        print('end:   ', datetime.now())


## Open GC file system using a locally-saved credential token
with open('path/to/authentication/file.json') as f:
    token = json.load(f)
    fs = gcsfs.GCSFileSystem(token=token)


# Transfer data to GC
for j in ['train', 'test']:
    for k in ['input', 'output']:
        ds = DS[j][k]
        mapper = fs.get_mapper(f'gs://leap-persistent/sungdukyu/E3SM-MMF_ne4.{j}.{k}.zarr')
        print(j, k)
        with ProgressBar():
            ds.to_zarr(mapper, mode='w')  # w for overwrite / a for append
