import requests
import os

# * Client code to interact with the Planet API * #

# Setup Planet Data API base URL
URL = "https://api.planet.com/data/v1"
# Setup the stats URL
stats_url = "{}/stats".format(URL)
# Setup the quick search endpoint url
quick_url = "{}/quick-search".format(URL)
# Specify the sensors/satellites or "item types" to include in our results
item_types = ["SkySatScene", "SkySatCollect"]

def initSession():
    """
    Open session with Planet API
    """
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


# -- Parse Features of a  quick-search response -

def getFeatures(geoJson):
    """
    Return a list of all features dict

    params:
    geoJson -> quick-search dict response

    """
    return geoJson["features"]


def getFeaturesLen(geoJson):
    """
    Return the number of items returned by a quick-search response

    params:
    geoJson -> quick-search dict response

    """
    return len(geoJson["features"])


def getFeaturesIds(geoJson):
    """
    Yield all item ids returned by a quick-search response
    max number of items == 250

    params:
    geoJson -> quick-search dict response
    """
    features = getFeatures(geoJson)
    if features:
        for f in features:
            yield f["id"]


def getFeatureIdx(geoJson, itemId):
    """
    Return index of a feature

    params:
        geoJson -> quick-search dict response
        itemId -> feature ID
    """
    for idx, _id in enumerate(getFeaturesIds(geoJson)):
        if _id == itemId:
            return idx
    raise Exception("Id: {} not found".format(itemId))


def getFeature(features, idx):
    """
    Return a feature

    params:
        features -> a features dict
        idx -> feature index
    """
    return features[idx]


def printItems(geoJsons):
    """
    Print all Features ids of all items resulted from multiple
    quick-search responses

    params:
        geoJsons -> list of multiple quick-search dict resposes
    """
    for idx, geoJson in enumerate(geoJsons, start=1):
        count = 0
        print("Start item: {}".format(idx))
        for _id in getFeaturesIds(geoJson):
            print("Id: {}".format(_id))
            count += 1
        print("Total items: {}".format(count))
        print("===== End item =====")
        print("")
