username, password = os.environ["EARTHDATA_USERNAME"], os.environ["EARTHDATA_PASSWORD"]
client_kwargs = {
    "auth": aiohttp.BasicAuth(username, password),
    "trust_env": True,
}

# the urls are a bit hard to construct, so lets try with a few hardcoded ones
urls = [
"https://ladsweb.modaps.eosdis.nasa.gov/archive/allData/62/MCD06COSP_M3_MODIS/2023/182/MCD06COSP_M3_MODIS.A2023182.062.2023223000656.nc",
"https://ladsweb.modaps.eosdis.nasa.gov/archive/allData/62/MCD06COSP_M3_MODIS/2023/213/MCD06COSP_M3_MODIS.A2023213.062.2023254000930.nc",
"https://ladsweb.modaps.eosdis.nasa.gov/archive/allData/62/MCD06COSP_M3_MODIS/2023/244/MCD06COSP_M3_MODIS.A2023244.062.2023285000449.nc",
]

MODIS_COSP = (
    beam.Create(pattern.items())
    | OpenURLWithFSSpec(
        open_kwargs={"block_size": 0, "client_kwargs": client_kwargs},
        max_concurrency=10,
    )
    | OpenWithXarray(
        file_type=pattern.file_type,
    )
    | Preprocess()
    | StoreToZarr(
        store_name="aqua-modis.zarr",
        combine_dims=pattern.combine_dim_keys,
        target_chunks={"time": 1, "lat": int(4320 / 2), "lon": int(8640 / 2)},
    )
)