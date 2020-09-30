import os
import geopandas as gpd
from datetime import datetime
import concurrent.futures
import pdb

import clientSatAPIs.utils as ut
import clientSatAPIs.planet_api as pa

from planet import api
from planet.api import filters

# * example script #


# *************** USING PLANET API ************************
date_filter = {
    "type": "DateRangeFilter", # Type of filter -> Date Range
    "field_name": "acquired",
    "config": {
        "gt": "2020-07-01T00:00:00.000Z",
        "lte": "2020-08-01T00:00:00.000Z",
    }
}

cloud_filter = {
    "type": "RangeFilter",
    "field_name": "cloud_cover",
    "config": {
        "lte": 20,
    }
}
download_filter = {
    "type": "PermissionFilter",
    "config": {
        "assets": "download",
    }
}
# Load polygons
g = gpd.read_file('../../Archive/Maria_Charcoal/studyvillages_WGS84.shx')
geoms = g['geometry'].values
shapesList = [ut.shapeToDict(i) for i in geoms]


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
                "config": [geo_filter, date_filter]
        }

        # Construct the request.
        request = {
                "item_types": pa.item_types,
                "filter": and_filter
                        }

        res_post = s.post(pa.quick_url, json=request)
        geoJsons.append(res_post.json())
    return geoJsons



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

def getFeaturesInBlocks(ls, inc):

    start = 0
    block = inc

    while start < len(ls):
        if block > len(ls):
            block = len(ls)
        yield ls[start:block]
        start = block
        block = block + inc

if __name__ == "__main__":

    BASEDIR = "/home/diego/work/dev/planet/clientSatAPIs_out/imgs_30072020"
    OUTDIR = "/media/diego/My Book/planet/August2020/imgs_August2020"

    assetTypes = ('basic_analytic', 'basic_analytic_udm2', 'ortho_analytic', 'ortho_analytic_udm2',
            'basic_panchromatic', 'basic_panchromatic_udm2', 'ortho_panchromatic', 'ortho_panchromatic_udm2',
            'ortho_visual')
    # ******* use planet client api
    #items = quick_search_client(shapesList)

    # ****** use planet api

    s = pa.initSession()
    #geoJsons = ut.readJson(os.path.join(BASEDIR, "geoJson.json"))
    geoJsons = quick_search(s, shapesList)

    for idx, geoJson in enumerate(geoJsons):
        print(f'feature {idx} with length: {pa.getFeaturesLen(geoJson)}')

    pdb.set_trace()
    uniqueFeatures = pa.getUniqueFeatures(geoJsons)
    print(f"{len(uniqueFeatures)} unique images to download")

    for at in assetTypes:
        while True:
            skipped = []
            for block in getFeaturesInBlocks(uniqueFeatures[:], 5):
                assetsLocations = []
                for f in block:
                    print(f"Feature id: {pa.getFeatureId(f)}")
                    location_url = pa.getAssetLocation(s, f, at)
                    if location_url:
                        assetsLocations.append(location_url)
                    else:
                        print(f"Could not activate {pa.getFeatureId(f)}, skipping..")
                        skipped.append(pa.getFeatureId(f))
                        continue

                for assetLoc in assetsLocations:
                    print(assetLoc)

                for assetLoc in assetsLocations:
                    pa.downloadAsset(assetLoc, OUTDIR)

            print(skipped)
            print(f"{len(skipped)} images not downloaded..try again..")
            if skipped:
                uniqueFeatures = pa.getSelectedFeatures(geoJsons, skipped)
            else:
                break
            print(f'All files donwloaded for asset: {at}')
            print('')
    print('All done')

