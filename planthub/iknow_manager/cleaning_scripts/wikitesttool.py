import csv
import math
import time

import pandas as pd
import requests

URL = 'https://query.wikidata.org/sparql'

# made them parameterized
# TODO: - look up here what is best practice when importing a python script (keyword .... def __MAIN__:)
# INPUT_FILE = 'planthub/iknow_manager/cleaning_scripts/halle_a.csv'
# OUTPUT_FILE = 'planthub/iknow_manager/cleaning_scripts/result.csv'
# NUM_QUERY_ENTITIES = 50

# TODO:
#   - write to disk, according to format (including INPUT_FILE data)

#   - make COLUMN an input parameter (atm just naive searching for df["Species"]) (NOT NOW)
#   - if query gets longer than ~~5900 characters, the endpoint returns a json error (NOT NOW)
#   --> make sure that if the query exceeds this limit, NUM_QUERY_ENTITIES changes (NOT NOW)


# builds query, sends request, returns response data evaluated as json
def get_wikidata_entities(query: str):
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


def build_query(labels, species_col=[]):
    query = '''
    SELECT DISTINCT * WHERE {
        '''

    for i, row in enumerate(labels):
        for j, label in enumerate(row):
            if j in species_col:
                query = add_species_label_query_piece(query, i*len(row)+j, label, True)
            else:
                query = add_string_label_query_piece(query, i*len(row)+j, label, True)

    # cut off the last union suffix
    query = query[0:-6]

    query += '''
        SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
    }
    '''

    return query


def add_species_label_query_piece(temp_query: str, i: int,
                                  label: str, union_suffix=False):
    if union_suffix:
        temp_query += '{' + f'?{i} rdfs:label "{label}"@en .\n '\
                            + f'?{i} wdt:P31 wd:Q16521 .' + '}\n' \
                            'UNION '
    else:
        temp_query += '{' + f'?{i} rdfs:label "{label}"@en .\n '\
                + f'?{i} wdt:P31 wd:Q16521 .' + '}\n'

    return temp_query


def add_string_label_query_piece(temp_query: str, i: int,
                                 label: str, union_suffix=False):
    if union_suffix:
        temp_query += '{' + f'?{i} rdfs:label "{label}"@en .\n '\
                            + '}\n' \
                            'UNION '
    else:
        temp_query += '{' + f'?{i} rdfs:label "{label}"@en .\n '\
                 + '}\n'

    return temp_query


# helpermethod to check if a specific key is present in the result
def list_of_dics_contains_key(value, dic_list):
    for element in dic_list:
        if list(dic_list.keys())[0] == value:
            return True

    return False


# write parts of the finished results to OUTPUT_FILE
def save_progress(rows, OUTPUT_FILE):
    with open(OUTPUT_FILE, 'a', newline='') as csvfile:
        spamwriter = csv.writer(csvfile, delimiter=',',
                                quotechar='"', quoting=csv.QUOTE_MINIMAL)

        for element in rows:
            spamwriter.writerow(element)


def progress_column(column, OUTPUT_FILE, NUM_QUERY_ENTITIES):
    col_length = len(column)

    # iterate content
    for i, x in enumerate(column):
        label_collector = []
        label_collector.append(x)

        # query every |NUM_QUERY_ENTITIES| entries
        if (i+1) % NUM_QUERY_ENTITIES == 0:
            save_progress(get_wikidata_entities(label_collector), OUTPUT_FILE, NUM_QUERY_ENTITIES)

            label_collector = []

        # FINISH
        if (i+1) == col_length:
            # reset NUM_QUERY_ENTITIES to write the correct number of rows
            # (maybe change this later)

            # at the moment commented out for flake8, check later if this MODULO is really not needed
            NUM_QUERY_ENTITIES = (i+1) % NUM_QUERY_ENTITIES
            save_progress(get_wikidata_entities(label_collector), OUTPUT_FILE, NUM_QUERY_ENTITIES)


def jsonResult_to_list(json, row_length: int, bin_col_types):
    # building helper list to store ordered results
    helper = []
    for x in range(len(json['head']['vars'])):
        helper.append([x])

    for i, result in enumerate(json['results']['bindings']):
        key = list(result.keys())[0]
        helper[int(key)].append(result[key]['value'])

    for i, element in enumerate(helper):
        if len(element) == 1:
            helper[i].append('NULL')

    helper = sorted(helper)

    resultList = []

    x = 0
    while (x < len(helper)):
        row = []
        for b in bin_col_types:
            if b == 0:
                row.append("")
            elif b == 1:
                row.append(helper[x][1])
                x += 1

        resultList.append(row)

    return resultList


def main(INPUT_FILE, OUTPUT_FILE, COL_TYPES, NUM_QUERY_ENTITIES=50):
    # ENTRY POINT
    # read file into memory
    print(f"Reading file: {INPUT_FILE}")
    df = pd.read_csv(INPUT_FILE)

    toSearchPerRow = 0
    species_columns = []
    bin_col_types = []
    for i, entry in enumerate(COL_TYPES):
        if entry == 'String':
            toSearchPerRow += 1
            bin_col_types.append(1)
        else:
            bin_col_types.append(0)
        if df.columns[i] == 'Species':
            species_columns.append(i)

    if toSearchPerRow <= 0:
        return False

    rowsPerQuery = math.floor(NUM_QUERY_ENTITIES/toSearchPerRow)

    label_collector = []
    for row in df.iterrows():
        label_helper = []
        for i, cell in enumerate(row[1]):
            if COL_TYPES[i] == 'String':
                label_helper.append(cell)

        label_collector.append(label_helper)

        if len(label_collector) == rowsPerQuery:
            json = get_wikidata_entities(build_query(label_collector,
                                                     species_columns))
            resultList = jsonResult_to_list(json,
                                            len(label_collector[0]),
                                            bin_col_types)

            save_progress(resultList, OUTPUT_FILE)
            label_collector = []

    # .. query and save all remaining labels and results
    if len(label_collector) > 0:
        json = get_wikidata_entities(build_query(label_collector,
                                                 species_columns))
        resultList = jsonResult_to_list(json,
                                        len(label_collector[0]),
                                        bin_col_types)

        save_progress(resultList, OUTPUT_FILE)
        label_collector = []

    # EXIT POINT
