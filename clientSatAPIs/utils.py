import os
import fnmatch
from shapely.geometry import mapping
import json


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


def writeJson(obj, outdir, filename):
    fpath = os.path.join(outdir, filename)
    with open(fpath, 'w') as outfile:
        json.dump(obj, outfile)


def readJson(fpath):
    with open(fpath) as json_file:
        return json.load(json_file)

def diff(total, partial):
    """
    Return a diff list: total - partial

    params:
    ------------

    total : list
    partial: list
    """
    return list(set(total) - set (partial))


def getFiles(dirpath, pattern):
    """
    Return all files in a dirpath
    with a file name matching a pattern
    """
    files = []
    # consider first level directory only
    for f in os.listdir(dirpath):
        if fnmatch.fnmatch(f, pattern):
            files.append(f)
    return files
