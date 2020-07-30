import os
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
