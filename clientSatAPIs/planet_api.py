import random
import requests
import time
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
# -- Assets related

def getFeatureAssets(s, assetsUrl):
    res = s.get(assetsUrl)
    return res


def activateAsset(s, activationUrl):
    res = s.get(activationUrl)
    if res == 202:
        print('request accepted')
    elif res == 204:
        print('asset already active, ready to download.')
        return res
    elif res == 401:
        raise Exception("Response status: {}".format(res.status_code))

def _backoff(s, url):
    # backoff if rate limit is exceeded
    max_attempts = 10
    attempts = 0
    while attempts < max_attempts:
        res = s.get(url)
        if res.status != 429:
            break
        # If rate limited, wait and try again
        time.sleep((2 ** attempts) + random.random())
        attempts = attempts + 1
    return res


def isAssetActive(s, assetsUrl, assetType):
    assetActivated = False
    while assetActivated == False:
        res = getFeatureAssets(s, assetsUrl)
        assets = res.json()

        assetStatus = assets[assetType]["status"]

		# If asset is already active, we are done
        if assetStatus == 'active':
            assetActivated = True
            print("Asset is active and ready to download")
        else:
            print("Not yet activated, sleeping for two seconds..")
            time.sleep(2)

    return assets[assetType]["location"]


def downloadAsset(assetLocationUrl, outdir, filename=None):
    # Send a GET request to the provided location url, using your API Key for authentication
    res = requests.get(assetLocationUrl, stream=True, auth=(os.environ['PLANET_API_KEY']))
    # If no filename argument is given
    if not filename:
        # Construct a filename from the API response
        if "content-disposition" in res.headers:
            filename = res.headers["content-disposition"].split("filename=")[-1].strip("'\"")
        # Construct a filename from the location url
        else:
            filename = assetLocationUrl.split("=")[1][:10]
    fpath = os.path.join(outdir, filename)
    # Save the file
    with open('output/' + fpath, "wb") as f:
        for chunk in res.iter_content(chunk_size=1024):
            if chunk: # filter out keep-alive new chunks
                f.write(chunk)
                f.flush()

    return fpath


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


def getFeaturePerm(feature):
    """
    Return a list of assets permission of a feature

    params:
        feature -> a feature
    """
    return feature["_permissions"]


def getFeatureGeometry(feature):
    """
    Return the geometry of a feature

    params:
        feature -> a feature
    """
    return feature["geometry"]


def getFeatureProperties(feature):
    """
    Return properties of a feature

    params:
        feature -> a feature
    """
    return feature["properties"]


def getFeatureId(feature):
    """
    Return the ID of a feature

    params:
        feature -> a feature
    """
    return feature["id"]


def getAssetUrl(feature):
    """
    Return the assets URL of a feature

    params:
        feature -> a feature
    """
    return feature["_links"]["assets"]


def getActivationUrl(assetType):
    """
    Return the activation URL of an asset type

    params:
        feature -> a feature
    """
    return assetType["_links"]["activate"]


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
