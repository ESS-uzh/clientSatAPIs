import random
import requests
import time
import os

import clientSatAPIs.utils as ut

import pdb

# * Client code to interact with the Planet API * #

# Setup Planet Data API base URL
URL = "https://api.planet.com/data/v1"
# Setup the stats URL
stats_url = "{}/stats".format(URL)
# Setup the quick search endpoint url
quick_url = "{}/quick-search".format(URL)
# Specify the sensors/satellites or "item types" to include in our results
item_types = ["SkySatScene", "SkySatCollect"]

# -- Assets related

def getFeatureAssets(s, assetsUrl):
    res = s.get(assetsUrl)
    return res


def getAssetUrl(feature):
    """
    Return the assets URL

    params:
        feature -> a feature
    """
    return feature["_links"]["assets"]

def getAssets(s, assetUrl):
    """
    Return the assets

    params:
        feature -> a feature
    """
    res = s.get(assetUrl)
    return res.json()


def getActivationUrl(assetType):
    """
    Return the activation URL for an asset

    params:
        assetType -> e.g. ortho_visual
    """
    return assetType["_links"]["activate"]


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


def getActiveAssetUrl(s, assetsUrl, assetType):
    assetActivated = False
    count = 1
    while assetActivated == False:
        res = getFeatureAssets(s, assetsUrl)
        assets = res.json()

        assetStatus = assets[assetType]["status"]

	# If asset is already active, we are done
        if assetStatus == 'active':
            assetActivated = True
            print("Asset is active and ready to download")
        else:
            if count > 3:
                return
            print("Not yet activated, sleeping for two seconds..")
            time.sleep(2)
            count += 1

    return assets[assetType]["location"]


def getAssetLocation(s, feature, assetType):
    # get asset url
    assetsUrl = getAssetUrl(feature)
    assets = getAssets(s, assetsUrl)
    # choose  assetType and get its url
    activationUrl = getActivationUrl(assets[assetType])
    # activate asset
    res = activateAsset(s, activationUrl)

    # get asset url location
    return getActiveAssetUrl(s, assetsUrl, assetType)


def downloadAsset(assetLocationUrl, outdir, filename=None):
    # Send a GET request to the provided location url, using your API Key for authentication
    res = requests.get(assetLocationUrl, stream=True, auth=(os.environ['PL_API_KEY'],""))
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
    with open(fpath, "wb") as f:
        for chunk in res.iter_content(chunk_size=1024):
            if chunk: # filter out keep-alive new chunks
                f.write(chunk)
                f.flush()

    return fpath


# -- Parse Features of a  quick-search response -

def getFileId(fname):
    """
    Extract the id from a filename
    """
    return '_'.join(fname.split('_')[:4])


def getUniqueFeatures(geoJsons):
    """
    Compute list of features with unique featureId
    
    Params
    ----------

    geoJsons : list
               multiple quick-search dict resposes
    Returns:
    ----------
    A list of unique features         
         
    """
    finalFeaturesIds = []
    finalFeatures = []
    for item in geoJsons:
        for f in getFeatures(item):
            if getFeatureId(f) in finalFeaturesIds:
                print(f"Feature: {getFeatureId(f)} already added, skipping..")
                continue
            finalFeaturesIds.append(getFeatureId(f))
            finalFeatures.append(f)
    return finalFeatures


def getFeaturesToDownload(uniqueFeatures, dirpath, pattern):
    """
    Compute features that were not downloaded
    
    Params
    ----------

    uniqueFeatures : list
                     total features 
    dirpath : string
              full path to directory of downloaded images

    pattern : string
              grab all files containing a string, e.g. *analytic*  
    

    Returns:
    ----------
    A list of features to download            
         
    """
    
    featuresToDownload = [] 
    idsDownloaded = [getFileId(f) for f in ut.getFiles(dirpath, pattern)]
    idsTotal = [getFeatureId(feature) for feature in uniqueFeatures]
    idsToDownload = ut.diff(idsTotal, idsDownloaded)
    
    for feature in uniqueFeatures:
        if getFeatureId(feature) in idsToDownload:
            print(f"feature id: {getFeatureId(feature)} to download..")
            featuresToDownload.append(feature)
    return featuresToDownload
    

def getUniqueAcquisitionDates(uniqueFeatures):
    """
    Extract unique dates of acquisition for a given list of features
    
    Params
    ----------

    uniqueFeatures : list
                     features 

    Returns:
    ----------
    A set of unique dates         
         
    """
    dates = []
    for feature in uniqueFeatures:
        _id = getFeatureId(feature)
        # append a date (first field of _id)
        dates.append(_id.split("_")[0])
    return set(dates)


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


