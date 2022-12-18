import time

import requests

URL = 'https://query.wikidata.org/sparql'


# builds query, sends request, returns response data evaluated as json
def send_query(query: str):
    fin = False
    jsonerrorcounter = 0
    timeoutcounter = 0

    while (not fin):
        # print("Sending request... Querylength: ", len(query))
        st = time.time()

        try:
            r = requests.post(URL, params={'format': 'json', 'query': query})
        except requests.exceptions.RequestException as e:
            # TODO: - handle error(s)
            print("Error during request: ", e)
            fin = True

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
    print("labels", labels)
    for i, label in enumerate(labels):

        query += '{ ' + \
            f'wd:{label[1]} wdt:P279 ?{i} .\n ?{i} rdfs:label ?{i}_label .\n FILTER (LANG(?{i}_label) = "en")' + \
            ' } UNION'

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
        if len(entry) == 0:
            continue
        key = next(iter(entry))
        # print(entry[key]['value'])
        result[key]['parentclasses'].append(entry[key]['value'])
        result[key]['parentlabel'].append(entry[key+"_label"]['value'])
    # print("result", result)

    return result


def main(header, OUTPUT_FILE):
    result = {}
    for i in range(len(header)):
        result[str(i)] = {}
        result[str(i)]['uri'] = header[i][1]
        result[str(i)]['slabel'] = header[i][0]
        result[str(i)]['parentclasses'] = []
        result[str(i)]['parentlabel'] = []
        header[i][1] = extract_Qlabel(header[i][1])

    # print("result in main", result)
    result = evaluate_response(send_query(build_query(header)), result)

    return result
