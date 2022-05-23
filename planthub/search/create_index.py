import copy
import os
from pathlib import Path

import pandas as pd
from elasticsearch_dsl import (
    Completion,
    Document,
    Integer,
    Keyword,
    Nested,
    Text,
    connections,
)

# es = Elasticsearch()
connections.create_connection(hosts=['localhost:9200'], timeout=20)

# data_path = 'C:\Daten\Documents\Projekte\plantHub\PlantHub\planthub\planthub\search\\'

# data_path = str(settings.APPS_DIR) + "/search/"
data_path = os.path.join(Path(__file__).resolve(strict=True).parent.parent, 'data')

df_data = pd.read_csv(os.path.join(data_path, 'PhenObs_2022-02-28 (1).csv'), encoding='unicode_escape',
                      low_memory=False)
df_genera = pd.read_csv(os.path.join(data_path, 'PlantHub genera_2022-05-13_v3.csv'), encoding='UTF-8',
                        low_memory=False, encoding_errors="replace")
df_family = pd.read_csv(os.path.join(data_path, 'PlantHub families_2022-05-10.csv'), encoding='UTF-8',
                        low_memory=False, encoding_errors="replace")
df_order = pd.read_csv(os.path.join(data_path, 'PlantHub orders_2022-05-10.csv'), encoding='UTF-8',
                       low_memory=False, encoding_errors="replace")


def mode_on_cols(df, key_col, value_cols):
    # First find all keys so we can the modes later
    result_df = copy.copy(df[key_col])
    result_df = result_df.to_frame(key_col)
    result_df.drop_duplicates(inplace=True)
    for col in value_cols:
        col_data_to_be_merged = df.groupby([key_col, col]).size() \
            .to_frame('count').reset_index() \
            .sort_values('count', ascending=False) \
            .drop_duplicates(subset=key_col)[[key_col, col]]
        result_df = result_df.merge(
            col_data_to_be_merged,
            on=key_col, how='outer',
        )
    return result_df


def aggregate_dataframe_on_species(df):
    # First we just declare some columns as categories/numerical. Nothing of importance is happening here
    columns = sorted(df.columns)
    discrete = [x for x in columns if df[x].dtype.name in ['object', 'category']]
    continuous = [x for x in columns if x not in discrete]
    cat_cols = [i for i in discrete if i != 'AccSpeciesName']
    numcols = [x for x in continuous if x != 'ObservationID']

    # Now we aggregate the categories
    species_df_cat = mode_on_cols(df, 'AccSpeciesName', cat_cols)
    # Now we aggregate the numerical data
    species_df_non_cat = df[['AccSpeciesName'] + numcols].groupby('AccSpeciesName').agg('mean')
    # Now we count, how many items each species has (stored in a columnt called 'count')
    count_df = df.groupby('AccSpeciesName').agg(count=('ObservationID', 'count'))
    # Now we merge the results together (first the categorical and non-categorical and then also the count)
    df_new = species_df_cat.merge(species_df_non_cat, on='AccSpeciesName', how='outer')
    df_new = df_new.merge(count_df, on='AccSpeciesName', how='outer')
    return df_new


def add_family(df):
    print(df_genera.head(40))
    # df_genera['EnglishName'].replace('"ë"','"ë"',inplace=True)
    # df_genera['GermanName'].replace('"ë"','"ë"',inplace=True)
    result_df = pd.merge(df, df_genera, on='AccGenus', how='left')
    return result_df


def add_order(df):
    result_df = pd.merge(df, df_family, on='Family', how='left')
    return result_df


def add_superorder(df):
    result_df = pd.merge(df, df_order, on='Order', how='left')
    return result_df


def rename_lang_cols(df, name):
    df.rename(columns={'EnglishName': name + '_EnglishName', 'GermanName': name + '_GermanName'}, inplace=True)
    return df


def add_hierachry(df):
    result_df_data = rename_lang_cols(df, "species")

    result_df_family = add_family(result_df_data)
    result_df_family = rename_lang_cols(result_df_family, "genus")

    result_df_order = add_order(result_df_family)
    result_df_order = rename_lang_cols(result_df_order, "family")

    df_superorder = add_superorder(result_df_order)
    df_superorder = rename_lang_cols(df_superorder, "order")

    return df_superorder


class PlantHubDatasetsIndex(Document):
    title = Text(fielddata=True, fields={'keyword': Keyword(), 'completion': Completion()})
    dataset_id = Integer()
    count = Integer()
    species = Keyword()
    genus = Keyword()
    family = Keyword()
    order = Keyword()
    superorder = Keyword()

    variables = Nested(
        multi=True,
        properties={
            'name_full': Text(fielddata=True, fields={'keyword': Keyword()}),
            'type': Text(fielddata=True, fields={'keyword': Keyword()}),
            'subtype': Text(fielddata=True, fields={'keyword': Keyword()}),
        }
    )

    class Index:
        name = "planthub_datasets_index"
        settings = {"number_of_shards": 1, "number_of_replicas": 0}


class PlantHubSpeciesIndex(Document):
    taxon_name = Completion(contexts=[{"name": "taxon_rank", "type": "category", "path": "taxon_rank"}])
    taxon_rank = Keyword()
    translation = Nested(
        multi=True,
        properties={
            'name': Text(fielddata=True, fields={'completion': Completion()}),
            'lang': Text(fielddata=True, fields={'keyword': Keyword()}),
            'taxon_name': Keyword(),
            'taxon_rank': Keyword()
        }
    )

    other_keywords = Nested(
        multi=True,
        properties={
            'name': Text(fielddata=True, fields={'keyword': Keyword(), 'completion': Completion()}),
        }
    )

    class Index:
        name = "planthub_species_index"
        settings = {"number_of_shards": 1, "number_of_replicas": 0}


class PlantHubVariableIndex(Document):
    variable_name = Text(fielddata=True, fields={'keyword': Keyword(), 'completion': Completion()})
    variable_description = Text()
    variable_type = Text(fielddata=True, fields={'keyword': Keyword(), 'completion': Completion()})
    variable_subtype = Text(fielddata=True, fields={'keyword': Keyword(), 'completion': Completion()})

    translation = Nested(
        multi=True,
        properties={
            'name': Text(fielddata=True, fields={'completion': Completion()}),
            'lang': Text(fielddata=True, fields={'keyword': Keyword()}),
            'ref_variable_name': Keyword()
        }
    )

    other_keywords = Nested(
        multi=True,
        properties={
            'name': Text(fielddata=True, fields={'keyword': Keyword(), 'completion': Completion()}),
        }
    )

    class Index:
        name = "planthub_variables_index"
        settings = {"number_of_shards": 1, "number_of_replicas": 0}


def set_values(found_arr, value):
    if value not in found_arr[0] and str(value) != "nan":
        found_arr[0].append(value)
        found_arr[1][value] = 1
    elif str(value) != "nan":
        found_arr[1][value] = found_arr[1][value] + 1

    return found_arr


def delete_index():
    # Delete all index and ignore if does not exists
    PlantHubDatasetsIndex._index.delete(ignore=[400, 404])
    PlantHubSpeciesIndex._index.delete(ignore=[400, 404])
    PlantHubVariableIndex._index.delete(ignore=[400, 404])


def set_translation(group, values, lang, taxon_rank, taxon_name):
    de_translation = str(values).split(',')
    for translation in de_translation:
        group['translation'].append({'name': translation.strip(), 'lang': lang,
                                     'taxon_rank': taxon_rank, 'taxon_name': taxon_name})
    return group


def set_taxon_rank(row, row_name, taxon_rank_name, with_translation=True):
    taxon_rank = {'scientific_name': row[row_name], 'translation': [], 'taxon_rank': taxon_rank_name}

    if with_translation:
        taxon_rank = set_translation(taxon_rank, row[taxon_rank_name + "_EnglishName"],
                                     'en', taxon_rank_name, taxon_rank['scientific_name'])
        taxon_rank = set_translation(taxon_rank, row[taxon_rank_name + "_GermanName"],
                                     'de', taxon_rank_name, taxon_rank['scientific_name'])
    print(taxon_rank)
    return taxon_rank


def create_index():
    # Create mapping for all index
    PlantHubDatasetsIndex.init()
    PlantHubSpeciesIndex.init()
    PlantHubVariableIndex.init()

    df_data_agg = aggregate_dataframe_on_species(df_data)
    result = add_hierachry(df_data_agg)

    for index, row in result.iterrows():
        taxon_list = []

        species = set_taxon_rank(row, 'AccSpeciesName', 'species')
        taxon_list.append(species)

        genus = set_taxon_rank(row, 'AccGenus', 'genus')
        taxon_list.append(genus)

        family = set_taxon_rank(row, 'Family', 'family')
        taxon_list.append(family)

        order = set_taxon_rank(row, 'Order', 'order')
        taxon_list.append(order)
        if str(row['superorder']) != 'nan':
            superorder = set_taxon_rank(row, 'superorder', 'superorder', False)
            taxon_list.append(superorder)

        variables = []
        for col in result.columns:
            # print(col)
            if str(row[col]) != 'nan':
                variables.append({'name_full': col, 'type': 'trait'})
                check = PlantHubVariableIndex.get(id=col.strip().replace(" ", "_"), ignore=404)
                if check is None:
                    new_entry = PlantHubVariableIndex(variable_name=col.strip().replace("_", " "), )
                    new_entry.meta.id = col.strip().replace(" ", "_")
                    new_entry.save()

        return_val = PlantHubDatasetsIndex(id=1, title="PhenObs", species=species['scientific_name'],
                                           genus=genus['scientific_name'], variables=variables,
                                           family=family['scientific_name'], order=order['scientific_name'],
                                           superorder=superorder['scientific_name'],
                                           count=row['count']).save(return_doc_meta=True)
        print(return_val)
        for taxon in taxon_list:
            check = PlantHubSpeciesIndex.get(id=taxon['scientific_name'].strip().replace(" ", "_"), ignore=404)
            if check is None:
                new_entry = PlantHubSpeciesIndex(taxon_name=taxon['scientific_name'],
                                                 translation=taxon['translation'], taxon_rank=taxon['taxon_rank'])
                new_entry.meta.id = taxon['scientific_name'].strip().replace(" ", "_")
                new_entry.save()

        # break


def delete_and_create():
    delete_index()
    create_index()

# delete_and_create()
