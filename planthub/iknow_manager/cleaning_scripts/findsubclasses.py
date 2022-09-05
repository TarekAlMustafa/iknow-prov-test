import time

import requests

URL = 'https://query.wikidata.org/sparql'


# builds query, sends request, returns response data evaluated as json
def send_query(query: str):
    fin = False
    jsonerrorcounter = 0
    timeoutcounter = 0

    while (not fin):
        print("Sending request... Querylength: ", len(query))
        st = time.time()
        r = requests.post(URL, params={'format': 'json', 'query': query})
        if str(r) != "<Response [429]>":
            try:
                data = r.json()
                fin = True
            except Exception as e:
                print("JSON EROR: ", e)
                jsonerrorcounter += 1
                fin = False
        else:
            time.sleep(1.0)
            timeoutcounter += 1

    dt = time.time() - st
    print(f"Query took: {dt}ms, with {jsonerrorcounter} json errors and {timeoutcounter} timeouts.")
    return data


def build_query(labels):
    query = '''
    SELECT * WHERE {
        '''

    for i, label in enumerate(labels):
        query += '{ ' + f'wd:{label} wdt:P279 ?{i}' + ' } UNION'

    # cut off the last union suffix
    query = query[0:-6]

    query += ' }'

    return query


def extract_Qlabel(wikidatalink: str):
    helper = ''
    for c in reversed(wikidatalink):
        helper = c + helper
        if c == 'Q':
            break

    return helper


def evaluate_response(json_data, result):
    findings = json_data['results']['bindings']
    for entry in findings:
        key = next(iter(entry))
        # print(entry[key]['value'])
        result[key]['parentclasses'].append(entry[key]['value'])

    return result


def main(header, OUTPUT_FILE):
    result = {}
    for i in range(len(header)):
        result[str(i)] = {}
        result[str(i)]['label'] = header[i]
        result[str(i)]['parentclasses'] = []
        header[i] = extract_Qlabel(header[i])

    result = evaluate_response(send_query(build_query(header)), result)

    return result
