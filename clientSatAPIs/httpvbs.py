
def buildGetRequest(s, url):
    """
    Send a get request to url endpoint

    params:
        s -> session
        url -> endpoint url

    Return a response obj
    """
    # Make a GET request to the Planet Data API
    res = s.get(url)
    # check that res  200 <= status code <= 400
    if not res:
        raise Exception("Response status: {}".format(res.status_code))
    # Response body
    return res


def buildPostRequest(s, url, request):
    """
    Send a post request to url endpoint

    params:
        s -> session
        url -> endpoint url
        request -> dict containing the request

    Return response obj
    """
    # Send the POST request to the API endpoint
    res = s.post(url, json=request)
    # check that res  200 <= status code <= 400
    if not res:
        raise Exception("Response status: {}".format(res.status_code))
    return res
