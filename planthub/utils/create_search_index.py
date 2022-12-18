import copy
import os
from pathlib import Path

import pandas as pd
from elasticsearch_dsl import connections

from ..search.models import (
    PlantHubDatasetsIndex,
    PlantHubSpeciesIndex,
    PlantHubVariableIndex,
)

#
# es = Elasticsearch()
connections.create_connection(hosts=['localhost:9200'], timeout=20)

# data_path = 'C:\Daten\Documents\Projekte\plantHub\PlantHub\planthub\planthub\search\\'

# data_path = str(settings.APPS_DIR) + "/search/"

print("Search loaded sadadssa")

data_path = os.path.join(Path(__file__).resolve(strict=True).parent.parent, 'data')

datasets = []
datasets.append({'file_name': 'PhenObs_2022-02-28 (1).csv', 'dataset_title': 'PhenObs'})


# datasets.append({'file_name': 'TRY_2022-05-09', 'dataset_title': 'TRY'})
# datasets.append({'file_name': 'sPlot_2022-02-28', 'dataset_title': 'sPlot'})


def read_files():
    global df_data, df_genera, df_family, df_order

    df_data = pd.read_csv(os.path.join(data_path, file_name), encoding='unicode_escape',
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
    # print(taxon_rank['scientific_name'])
    return taxon_rank


def create_index():
    # Create mapping for all index
    PlantHubDatasetsIndex.init()
    PlantHubSpeciesIndex.init()
    PlantHubVariableIndex.init()

    read_files()

    df_data_agg = aggregate_dataframe_on_species(df_data)
    # df_data_agg.to_csv("agg_test.csv")
    result = add_hierachry(df_data_agg)
    # result.to_csv("agg_test_full.csv")

    for index, row in result.iterrows():
        taxon_list = []
        subspecies = {'scientific_name': None, 'subspecies_EnglishName': None, 'subspecies_GermanName': None}

        if row['AccSpeciesName'] != None and len(row['AccSpeciesName'].split(" ")) > 2:
            row['subspecies_EnglishName'] = row['species_EnglishName']
            row['species_EnglishName'] = None
            row['subspecies_GermanName'] = row['species_GermanName']
            row['species_GermanName'] = None
            subspecies = set_taxon_rank(row, 'AccSpeciesName', 'subspecies')
            taxon_list.append(subspecies)

            row['Species'] = " ".join(row['AccSpeciesName'].split(" ")[:2])
            species = set_taxon_rank(row, 'Species', 'species')
            taxon_list.append(species)
        else:
            species = set_taxon_rank(row, 'AccSpeciesName', 'species')
            taxon_list.append(species)

        if str(row['AccGenus']) != 'nan':
            genus = set_taxon_rank(row, 'AccGenus', 'genus')
            taxon_list.append(genus)

        if str(row['Family']) != 'nan':
            family = set_taxon_rank(row, 'Family', 'family')
            taxon_list.append(family)

        if str(row['Order']) != 'nan':
            order = set_taxon_rank(row, 'Order', 'order')
            taxon_list.append(order)

        if str(row['superorder']) != 'nan':
            superorder = set_taxon_rank(row, 'superorder', 'superorder', False)
            taxon_list.append(superorder)

        if str(row['subclass']) != 'nan':
            subclass = set_taxon_rank(row, 'subclass', 'subclass', False)
            taxon_list.append(subclass)

        if str(row['class']) != 'nan':
            class1 = set_taxon_rank(row, 'class', 'class', False)
            taxon_list.append(class1)

        variables = []
        for col in result.columns:
            # print(col)
            if str(row[col]) != 'nan':
                variables.append({'name_full': col, 'type': 'trait'})  # todo add correct type here
                check = PlantHubVariableIndex.get(id=col.strip().replace(" ", "_"), ignore=404)
                if check is None:
                    new_entry = PlantHubVariableIndex(variable_name=col.strip().replace("_", " "), )
                    new_entry.meta.id = col.strip().replace(" ", "_")
                    new_entry.save()

        PlantHubDatasetsIndex(id=1, title=dataset_title, species=species['scientific_name'],
                              subspecies=subspecies['scientific_name'],
                              genus=genus['scientific_name'], variables=variables,
                              family=family['scientific_name'], order=order['scientific_name'],
                              superorder=superorder['scientific_name'], subclass=subclass['scientific_name'],
                              class1=class1['scientific_name'],
                              count=row['count']).save(return_doc_meta=True)
        print(species['scientific_name'])
        # print(return_val)

        for taxon in taxon_list:
            check = PlantHubSpeciesIndex.get(id=taxon['scientific_name'].strip().replace(" ", "_"), ignore=404)
            if check is None:
                new_entry = PlantHubSpeciesIndex(taxon_name=taxon['scientific_name'],
                                                 translation=taxon['translation'], taxon_rank=taxon['taxon_rank'])
                new_entry.meta.id = taxon['scientific_name'].strip().replace(" ", "_")
                new_entry.save()

        # break


def delete_and_create():
    global file_name, dataset_title
    delete_index()
    for dataset in datasets:
        file_name = dataset['file_name']
        dataset_title = dataset['dataset_title']
        create_index()

# delete_and_create()
# create_index()
