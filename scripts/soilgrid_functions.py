import rasterio as rio
import requests
import os
import glob
import sys
from rasterio.merge import merge
from rasterio.coords import BoundingBox
from shapely.geometry import Polygon

SOIL_LAYERS = {"Organic carbon density": "ocd",
               "Soil organic carbon stock": "ocs",
               "Bulk density": "bdod",
               "Clay content": "clay",
               "Coarse fragments": "cfvo",
               "Sand": "sand",
               "Silt": "silt",
               "Cation exchange capacity": "cec",
               "Nitrogen": "nitrogen",
               "Soil organic carbon": "soc",
               "pH water": "phh2o"}

AVAILABLE_DEPTHS = ["0-5"]
ocs_depth = "0-30"


def soilgrid_request(outputdir, layer, minlong, maxlong, minlat, maxlat):
    sproperty = layer[:layer.index('_')]
    ## set the url request
    url = (
        "https://maps.isric.org/mapserv?map=/map/{}.map&SERVICE=WCS&VERSION=2.0.1&REQUEST=GetCoverage&COVERAGEID={}&FORMAT=image/tiff&SUBSET=long({},{})&SUBSET=lat({},{})&SUBSETTINGCRS=http://www.opengis.net/def/crs/EPSG/0/4326&OUTPUTCRS=http://www.opengis.net/def/crs/EPSG/0/4326").format(
        sproperty, layer, minlong, maxlong, minlat, maxlat)

    r = requests.get(url)
    fileexportname = '{}_{}_{}_{}_{}_temp.tif'.format(layer, minlong, maxlong, minlat, maxlat)
    outputpath = os.path.join(outputdir, fileexportname)
    if "200" in str(r):
        with open(outputpath, 'wb') as f:
            f.write(r.content)
        #print(fileexportname + ' file was download')
    else:
        print(fileexportname + ' file was not posible to download\ncheck longitude and latitude distance or run again')


def getCoordinatePixel(raster_path, lon, lat, n=1):
    # open map
    with rio.open(raster_path) as dataset:
        # get pixel x+y of the coordinate
        py, px = dataset.index(lon, lat)
        # create 1x1px window of the pixel
        window = rio.windows.Window(px - n // 2, py - n // 2, n, n)
        # read rgb values of the window
        clip = dataset.read(window=window)

    return (clip)


def get_soilgridpixelvalue(layer, long, lat, donwload=True):
    """ Get soilgrid data from either soilgrid repository or a local folder"""

    if donwload:

        if not (os.path.exists("temp")):
            os.mkdir("temp")

        long = float(long)
        lat = float(lat)
        increase = float(3)
        minimum_longitude = (long - increase)
        maximum_longitude = (long + increase)
        minimum_latitude = (lat - increase)
        maximum_latitude = (lat + increase) #if lat >= 0 else (lat + increase)
        if layer == "Soil organic carbon stock":
            depth = "0-30"
        else:
            depth = AVAILABLE_DEPTHS[0]

        final_name = "temp/{}_{}cm_mean.tif".format( SOIL_LAYERS[layer], depth)
        if os.path.exists(final_name):

            coord_sys = [[long + 0.001, lat - 0.001],
                         [long - 0.001, lat - 0.001],
                         [long - 0.001, lat + 0.001],
                         [long + 0.001, lat + 0.001]]

            pol_r = Polygon(coord_sys)

            with rio.open(final_name) as src:
                metada = src.meta.copy()

            percentage = get_intersetion_polygons(pol_r, getraster_boundingbox(metada))

            if percentage > 90:
                path = final_name
            else:
                path = download_soilgrid_data("temp",
                                      layer,
                                      [minimum_longitude, maximum_longitude,
                                       minimum_latitude, maximum_latitude],
                                      depth=depth)
        else:
            path = download_soilgrid_data("temp",
                                          layer,
                                          [minimum_longitude, maximum_longitude,
                                           minimum_latitude, maximum_latitude],
                                          depth=depth)

    soilgridvalue = getCoordinatePixel(path, long, lat)

    if len(soilgridvalue[0]) > 0:
        soilgridvalue = soilgridvalue[0][0][0]
    else:
        soilgridvalue = 0
    return soilgridvalue


def download_soilgrid_data(output_path, soillayer, boundary_box, depth="0-5"):
    """Dowload a soilgrid layer data using a boundary box
    for more information please check out https://soilgrids.org/
    Parameters
           ----------
           output_path : str
                   string path to a destination folder
           soillayer : str
                  soilgrid name layer, check soillayers table
           boundary_box : list
                   list that contains [min longitude, max longitude, min latitude, max latitude]
           depth : list str
                   the depth of interest  there are currentyly ["0-5", "5-15", "15-30", "30-60", "60-100", "100-200"]

    Output
          ----------
          Tiff files

    """

    ## setting the layer name
    layer = SOIL_LAYERS[soillayer]
    ## exception for Soil organic carbon stock
    if layer == "ocs" and depth != "0-30":
        print("0-30cm depth is the only one available for this product {}".format(soillayer))
        sys.exit(1)

    layer = "{}_{}cm_mean".format(layer, depth)

    ## setting longitudes and latitudes

    minlong, maxlong, minlat, maxlat = boundary_box

    lat = minlat

    while lat < maxlat:
        long = minlong
        mn_lat = lat
        mx_lat = lat + 2

        while long < maxlong:
            mn_long = long
            mx_long = long + 2
            soilgrid_request(output_path, layer, mn_long, mx_long, mn_lat, mx_lat)
            long += 2
        lat += 2

    ## merge tiles
    pattern = '*temp.tif'
    files_to_mosaic = glob.glob(os.path.join(output_path, pattern))
    image, metadaa = merge_tiles(files_to_mosaic)
    fileexportname = '{}.tif'.format(layer)

    ## write file
    out_fp = os.path.join(output_path, fileexportname)
    with rio.open(out_fp, "w", **metadaa) as dest:
        dest.write(image)

    print(fileexportname + ' file was created')

    ## remove temporary files
    remove_files(files_to_mosaic)

    return out_fp


def remove_files(file_list):
    for fp in file_list:
        os.remove(fp)


def merge_tiles(rasterfilepaths):
    """ Function created for merging multiple raster files using
    rasterio"""

    ## reading files
    src_files_to_mosaic = []
    for fp in rasterfilepaths:
        src = rio.open(fp)
        src_files_to_mosaic.append(src)

    mosaic, out_trans = merge(src_files_to_mosaic)

    out_meta = src.meta.copy()

    # Update the metadata
    out_meta.update({"driver": "GTiff",
                     "height": mosaic.shape[1],
                     "width": mosaic.shape[2],
                     "transform": out_trans,
                     "crs": src.meta.copy()['crs']
                     })

    return [mosaic, out_meta]


def getraster_boundingbox(metadata):
    # get boundaries
    img_bounds = list(
        rio.transform.array_bounds(metadata['height'], transform=metadata['transform'],
                                        width=metadata['width']))
    ## organice data
    img_bounds = BoundingBox(left=img_bounds[0], bottom=img_bounds[1], right=img_bounds[2],
                             top=img_bounds[3])

    image_wkt = [(img_bounds[0], img_bounds[3]),
                 (img_bounds[0], img_bounds[1]),
                 (img_bounds[2], img_bounds[1]),
                 (img_bounds[2], img_bounds[3])]

    return Polygon(image_wkt)


def get_intersetion_polygons(pol_ref, pol_img):
    ## get reference polygon

    p_intersected = pol_ref.intersection(pol_img)

    # calculate area
    area_intersected = p_intersected.area * 100 / pol_ref.area
    return area_intersected

