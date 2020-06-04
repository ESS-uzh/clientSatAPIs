import geopandas as gpd
from shapely.geometry import mapping
import json
import requests
import os

# * Planet data API * #


def _initSession():
    # Setup the API Key from the `PL_API_KEY` environment variable
    PLANET_API_KEY = os.getenv('PL_API_KEY')
    if PLANET_API_KEY:
        # Setup the session
        session = requests.Session()
        # Authenticate
        session.auth = (PLANET_API_KEY, "")
        return session
    raise Exception("No api key found. Please check for PL_API_KEY "
                    "env variable on your system. "
                    "\n"
                    "To export it: "
                    "export PL_API_KEY='YOUR API KEY HERE'")


def buildGetRequest(s, url):
    """
    Send a get request to url endpoint

    params:
        s -> session
        url -> endpoint url

    Return a dict response
    """
    # Make a GET request to the Planet Data API
    res = s.get(url)
    # check that res  200 <= status code <= 400
    if not res:
        raise Exception("Response status: {}".format(res.status_code))
    # Response body
    return res.json()


def buildiPostRequest(s, url, item_types, _filter):
    """
    Send a post request to url endpoint

    params:
        s -> session
        url -> endpoint url
        item_types -> sensor type
        _filter -> a request filter

    Return a dict response
    """
    # Construct the request.
    request = {
        "item_types": item_types,
        "filter": _filter
    }
    # Send the POST request to the API endpoint
    res = s.post(url, json=request)
    # check that res  200 <= status code <= 400
    if not res:
        raise Exception("Response status: {}".format(res.status_code))
    return res.json()


def getFeaturesLen(geoJson):
    """
    Return the number of items returned by a quick-search response


    geoJson -> quick-serch dict response

    """
    return len(geoJson["features"])


def getIds(geoJson):
    """
    Yield all item ids returned by a quick-search response
    max number of items == 250

    geoJson -> quick-serch dict response
    """
    features = geoJson["features"]
    if features:
        for f in features:
            yield f["id"]


def printItems(geoJsons):
    """
    Print all item ids resulted from multiple quick-search responses

    params:
        geoJsons -> list of multiple quick-search dict resposes
    """
    for idx, geoJson in enumerate(geoJsons, start=1):
        count = 0
        print("Start item: {}".format(idx))
        for _id in getIds(geoJson):
            print("Id: {}".format(_id))
            count += 1
        print("Total items: {}".format(count))
        print("===== End item =====")
        print("")


# Helper function to printformatted JSON using the json module
def p(data):
    print(json.dumps(data, indent=2))


def shapeToDict(shapeObj):
    """
    Convert a shape object into a dict.
    3D Polygons are converted to 2D

    params:
        shapeObj -> shapely.geometry.Polygon

    """
    d = mapping(shapeObj)
    if d["type"] == "Polygon" and len(d["coordinates"][0][0]) > 2:
        # remove Z coordinate
        coordTwoD = [[i[:2] for i in d['coordinates'][0]]]
        return {"type": "Polygon", 'coordinates': coordTwoD}
    return d

if __name__ == "__main__":

    s = _initSession()
    # Setup Planet Data API base URL
    URL = "https://api.planet.com/data/v1"
    res = buildGetRequest(s, URL)
    # Print the value of the item-types key from _links
    print(res["_links"]["item-types"])

    # Setup the stats URL
    stats_url = "{}/stats".format(URL)
    # Setup the quick search endpoint url
    quick_url = "{}/quick-search".format(URL)
    # Specify the sensors/satellites or "item types" to include in our results
    item_types = ["SkySatScene", "SkySatCollect"]

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
    g = gpd.read_file('Maria_Charcoal/studyvillages_WGS84.shx')
    geoms = g.geometry.values
    shapesList = [shapeToDict(i) for i in geoms]

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
        geoJsons.append(buildiPostRequest(s, quick_url,
                                          item_types, and_filter))


    printItems(geoJsons)
