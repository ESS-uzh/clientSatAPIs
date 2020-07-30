import datatime
import geopandas as gpd
import utils as ut
import planet_api as pa

# * example script #

# Set filters
date_filter = {
    "type": "DateRangeFilter", # Type of filter -> Date Range
    "field_name": "acquired",
    "config": {
        "gt": "2019-12-01T00:00:00.000Z",
    }
}

cloud_filter = {
    "type": "RangeFilter",
    "field_name": "cloud_cover",
    "config": {
        "lte": 0.1,
    }
}
# Load polygons
g = gpd.read_file('../../Maria_Charcoal/studyvillages_WGS84.shx')
geoms = g['geometry'].values
shapesList = [ut.shapeToDict(i) for i in geoms]


if __name__ == "__main__":

    s = pa.initSession()
    res_get = s.get(pa.URL)
    # Print the value of the item-types key from _links
    print(res_get.json()["_links"]["item-types"])

#
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


    #printItems(geoJsons)

    # example - get location url of an asset for download
    # get a feature 0 from item 2
    #f0i2 = getFeature(getFeatures(geoJsons[2]), 0)
    #assets_url = f0i2["_links"]["assets"]
    #res = hv.buildGetRequest(s, assets_url)
    #assests = res.json()
    #ovisual = assests["ortho_visual"]
    #activation_url = ovisual["_links"]["activate"]
    #res = hv.buildGetRequest(s, activation_url)
    #assests = res.json()
    #ovisual = assests["ortho_visual"]
    #ovisual["status"]
    #location_url = ovisual["location"]
