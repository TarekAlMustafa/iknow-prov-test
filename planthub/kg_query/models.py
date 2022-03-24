import json

import requests
from django.conf import settings


def generate_sparql_select():
    query = b'select * where { ?s ?p ?o }'

    return query


def send_request_to_blazegraph():
    url = settings.BLAZEGRAPH_URL + 'bigdata/sparql'

    # header should be fix in backend for now
    headers = {
        'Accept': 'application/sparql-results+json,text/turtle'
    }

    params = {'query': generate_sparql_select()}

    # data = 'query=SELECT * { ?s ?p ?o }'

    # requests.post für SPARQL queries currently returns IncompleteRead error
    # TODO: Find solution for POST
    response = requests.get(url=url, params=params, data=None, headers=headers)

    return json.loads(response.content)
