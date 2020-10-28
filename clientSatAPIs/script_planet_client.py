import os
import requests
import geopandas as gpd
from datetime import datetime
import concurrent.futures
import pdb

import clientSatAPIs.utils as ut
import clientSatAPIs.planet_api as pa

from planet import api
from planet.api import filters

# ***************** USING Planet PYTHON CLIENT *********************
client = api.ClientV1()
start_date = datetime(year=2020, month=8, day=1)

date_filter_cl = filters.date_range('acquired', gte=start_date)
cloud_filter_cl = filters.range_filter('cloud_cover', lte=0.1)


def quick_search_client(shapesList):

    items = []
    for shape in shapesList:
        geo_filter = {
            "type": "GeometryFilter",
            "field_name": "geometry",
            "config": shape
        }

        # Setup an "AND" logical filter
        and_filter = filters.and_filter(date_filter_cl, cloud_filter_cl, geo_filter)

        # Construct the request.
        req = filters.build_search_request(and_filter, pa.item_types)
        res = client.quick_search(req)
        items.append(res)
    return items


#######################################################################

if __name__ == "__main__":

    BASEDIR = "/mnt/planet_data/"
    
    # Load polygons
    g = gpd.read_file(os.path.join(BASEDIR, "Archive/Maria_Charcoal/studyvillages_WGS84.shx"))
    geoms = g['geometry'].values
    shapesList = [ut.shapeToDict(i) for i in geoms]

    OUTDIR = os.path.join(BASEDIR, "october2020")
    
    # ******* use planet client api
    items = quick_search_client(shapesList)
