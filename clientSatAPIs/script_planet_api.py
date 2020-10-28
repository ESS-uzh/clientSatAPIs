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


# *************** USING PLANET API ************************

date_filter = {
    "type": "DateRangeFilter", # Type of filter -> Date Range
    "field_name": "acquired",
    "config": {
        "gt": "2020-09-01T00:00:00.000Z",
        "lte": "2020-09-20T00:00:00.000Z",
    }
}

cloud_filter = {
    "type": "RangeFilter",
    "field_name": "cloud_cover",
    "config": {
        "lte": 14,
    }
}
download_filter = {
    "type": "PermissionFilter",
    "config": {
        "assets": "download",
    }
}


def quick_search(s, shapesList):

    geoJsons = []
    for shape in shapesList:
        geo_filter = {
            "type": "GeometryFilter",
            "field_name": "geometry",
            "config": shape
        }

        # Setup an "AND" logical filter
        and_filter = {
                "type": "AndFilter",
                "config": [geo_filter, date_filter, cloud_filter]
        }

        # Construct the request.
        request = {
                "item_types": pa.item_types,
                "filter": and_filter
                        }

        res_post = s.post(pa.quick_url, json=request)
        geoJsons.append(res_post.json())
    return geoJsons


# -- Helpers

def getBlocks(ls, inc):
    """
    Yield list content in blocks of size inc

    """

    start = 0
    block = inc

    while start < len(ls):
        if block > len(ls):
            block = len(ls)
        yield ls[start:block]
        start = block
        block = block + inc

        
if __name__ == "__main__":

    BASEDIR = "/mnt/planet_data/"
    
    # Load polygons
    g = gpd.read_file(os.path.join(BASEDIR, "Archive/Maria_Charcoal/studyvillages_WGS84.shx"))
    geoms = g['geometry'].values
    shapesList = [ut.shapeToDict(i) for i in geoms]

    OUTDIR = os.path.join(BASEDIR, "september2020")
    
    assetTypes = ['ortho_analytic', 'ortho_analytic_udm2', 'ortho_panchromatic', 'ortho_panchromatic_udm2']

    # Setup the API Key from the `PL_API_KEY` environment variable
    PLANET_API_KEY = os.getenv('PL_API_KEY')
    if not PLANET_API_KEY:
        raise Exception("No api key found. Please check for PL_API_KEY "
                    "env variable on your system. "
                    "\n"
                    "To export it: "
                    "export PL_API_KEY='YOUR API KEY HERE'")

    with requests.Session() as s:
        
        s.auth = (PLANET_API_KEY, "")

        #geoJsons = ut.readJson(os.path.join(BASEDIR, "geoJson.json"))
        geoJsons = quick_search(s, shapesList)

        for idx, geoJson in enumerate(geoJsons):
            print(f'feature {idx} with length: {pa.getFeaturesLen(geoJson)}')
        #features = pa.getUniqueFeatures(geoJsons) 
        for at in assetTypes:
            uniqueFeatures = pa.getUniqueFeatures(geoJsons)
            print(pa.getUniqueAcquisitionDates(uniqueFeatures))
            #uniqueFeatures = pa.getFeaturesToDownload(features, OUTDIR, '*analytic*')
            print(f"{len(uniqueFeatures)} unique Feature to process..")
            print(f"Start procedure for assetType: {at}")
            while True:
                skipped = []
                for block in getBlocks(uniqueFeatures, 5):
                    assetsLocations = []
                    for f in block:
                        print(f"Feature id: {pa.getFeatureId(f)}")
                        location_url = pa.getAssetLocation(s, f, at)
                        if location_url:
                            assetsLocations.append(location_url)
                        else:
                            print(f"Could not activate {pa.getFeatureId(f)}, skipping..")
                            skipped.append(f)
                            continue

                    for assetLoc in assetsLocations:
                        print(assetLoc)

                    for assetLoc in assetsLocations:
                        pa.downloadAsset(assetLoc, OUTDIR)

                if skipped:
                    print(f"{len(skipped)} features not processed..try again..")
                    uniqueFeatures = skipped
                else:
                    print(f'All files donwloaded for asset: {at}')
                    print('')
                    break
        print('All done')

