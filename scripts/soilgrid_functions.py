import rasterio as rio

def getCoordinatePixel(raster_path,lon,lat, n = 1):
    # open map
    with rio.open(raster_path) as dataset:
        # get pixel x+y of the coordinate
        py, px = dataset.index(lon, lat)
        # create 1x1px window of the pixel
        window = rio.windows.Window(px - n//2, py - n//2, n, n)
        # read rgb values of the window
        clip = dataset.read(window=window)

    return(clip)


def get_soilgridpixelvalue(path, long, lat):

    soilgridvalue = getCoordinatePixel(path, long, lat)

    if len(soilgridvalue[0]) > 0:
        soilgridvalue = soilgridvalue[0][0][0]
    else:
        soilgridvalue = 0
    return soilgridvalue