# THis file is saving information about a SGPC.

from django.core.exceptions import ObjectDoesNotExist
from django.http import JsonResponse

from planthub.iknow_sgp.models import SGP
from planthub.iknow_sgp.views import (
    sgp_append_cpa_step,
    sgp_append_schema_step,
    sgp_in_progress,
    sgp_replace_mapping_file_with_copy,
)

from planthub.iknow_manager.models import get_property_url_by_label

from planthub.iknow_manager.cleaning_scripts.wikitesttool import jsonResult_to_list, get_wikidata_entities, build_query

from .models import SGPC, BioProject


def sgpc_create(request):
    """
    Creates a new SGP instance connected to a given Bioproject.
    Bioproject can be selected or newly created.
    Returns sgpc.pk of the new instance on success.
    """
    data: dict = request.data

    if not type(data) == dict or 'data' not in data.keys():
        return JsonResponse({"error": "invalid request format"})

    # name chosen by client
    choice = data['data']['bioprojectname']

    # client wants to select the project from existing ones
    userName = request.GET.get('userName', default='Admin')
    if data['data']['projectChoice'] == 'select':
        for proj in BioProject.objects.all():
            if proj.name == choice:
                new_collection = SGPC()
                new_collection.bioprojectname = proj.name
                new_collection.createdBy = userName
                new_collection.save()
                return JsonResponse({"project_id": new_collection.pk})
    # client wants to create a new project
    elif data['data']['projectChoice'] == 'create':
        if not BioProject.name_exists(choice):
            newProject = BioProject()
            newProject.name = choice            
            new_collection.createdBy = userName
            newProject.save()

        new_collection = SGPC()
        new_collection.bioprojectname = choice
        new_collection.save()

        return JsonResponse({"project_id": new_collection.pk})


def sgpc_from_key(key: str):
    """
    Returns a safely obtained instance of SGPC
    from a given key.
    """
    if key is None:
        return False

    # get sgpc instance
    try:
        sgpc: SGPC = SGPC.objects.get(id=key)
    except ObjectDoesNotExist:
        # sgpc_pk was no valid primary key
        return False

    return sgpc


def sgpc_info():
    """
    Returns information about all sgpc in the database,
    for the client to display and choose from.
    """
    # table header
    info = [['Collectionname', 'Bioprojectname', '# associated graphs']]

    sgpc: SGPC
    for sgpc in SGPC.objects.all():
        info.append([sgpc.collectionname, sgpc.bioprojectname, sgpc.associated_sgprojects.all().count(), sgpc.pk])

    return info


def sgpc_info_by_collection_name(list_of_collectionsID):
    """
    Returns information about all sgpc in the database,
    for the client to display and choose from.
    """
    # table header
    info = [['Collectionname', 'Bioprojectname', '# associated graphs']]

    sgpc: SGPC
    for sgpc in SGPC.objects.all():
        split_collectionname = sgpc.collectionname.split("_")

        if len(split_collectionname) > 1 and split_collectionname[1] in list_of_collectionsID:
            info.append([sgpc.collectionname, sgpc.bioprojectname, sgpc.associated_sgprojects.all().count(), sgpc.pk])

    return info


def sgpc_in_progress(sgpc: SGPC):
    """
    Checks if tool is running for a given sgpc.
    Calls is_in_progress on each sgp.
    """

    for sgp in sgpc.associated_sgprojects.all():
        if sgp_in_progress(sgp):
            return True

    # no sgp is still in progress
    return False


def sgpc_history(sgpc: SGPC):
    """
    Returns history for a single sgpc.
    """
    sgp0 = sgpc.associated_sgprojects.all()[0]

    helper = []
    for key, phase in sgp0.provenanceRecord.items():
        helper.append([key, phase['type']])

    return helper


def sgpc_history_renamed(sgpc: SGPC):
    """
    Returns renamed history for a single sgpc.
    For display in frontend.
    """
    sgp0 = sgpc.associated_sgprojects.all()[0]

    helper = []
    for key, phase in sgp0.provenanceRecord.items():
        name = ""
        cur_type = phase['type']

        if cur_type == 'linking':
            name = "Linking"
        if cur_type == 'cleaning':
            name = "Cleaning"
        if cur_type == 'init':
            name = "Initialization"
        if cur_type == 'editcpa':
            name = "Property Declaration"
        if cur_type == 'editmapping':
            name = "Cells Linking (after editing)"
        if cur_type == 'schemarefine':
            name = "Schema Refinement"
        if cur_type == 'querybuilding':
            name = "Query Building"
        if cur_type == 'downloading':
            name = "Saving- Pushing"

        helper.append([key, name])

    return helper


def sgpc_undo_till_phase(sgpc: SGPC, phase_number: int):
    """
    Clears provenance Record of SGPC and all its SGPs until
    given phase_number.
    """

    for sgp in sgpc.associated_sgprojects.all():
        prov_rec = sgp.provenanceRecord
        for i in range(len(sgp.provenanceRecord)-1, phase_number-1, -1):
            try:
                cur_type = prov_rec[str(i)]['type']
            except KeyError:
                # TODO: - handle error (if this happens, provrec is broken)
                continue

            # handling for each phase type
            if cur_type == "linking":
                del prov_rec[str(i)]
                # TODO: Clear datasets

            elif cur_type == "cleaning":
                del prov_rec[str(i)]

            elif cur_type == "editcpa":
                del prov_rec[str(i)]

                for key, phase in sgpc.collection_prov_rec.items():
                    if phase['type'] == "editcpa":
                        del sgpc.collection_prov_rec[key]
                        break

                sgpc.cpaMappings = {}
            elif cur_type == "editmapping":
                del prov_rec[str(i)]

            elif cur_type == "schemarefine":
                del prov_rec[str(i)]
                for key, phase in sgpc.collection_prov_rec.items():
                    if phase['type'] == "schemarefine":
                        del sgpc.collection_prov_rec[key]
                        break

                sgpc.subclassMappings = {}

            elif cur_type == "init":
                del prov_rec[str(i)]

        sgp.save()

    sgpc.save()


def sgpc_copy(sgpc: SGPC):
    """
    Copies a collection (and copies all its SGPs),
    replaces the mapping file and returns
    the newly created copied SGPC object.
    """
    copied_sgps = []

    sgp: SGP
    for sgp in sgpc.associated_sgprojects.all():
        # get source dataset of sgp
        try:
            dataset = sgp.source_dataset.all()[0]
        except IndexError:
            # TODO: - handle error
            continue

        # copy sgp
        sgp.pk = None
        # sgp.id = None
        sgp.project_copied = True
        sgp.datasets_copied = True

        sgp.save()

        # add original source dataset to sgp_copy
        sgp.source_dataset.add(dataset)

        try:
            sgp_replace_mapping_file_with_copy(sgp)
        except ValueError:
            # TODO: - handle error
            continue

        copied_sgps.append(sgp)

    # copy sgpc
    sgpc.pk = None
    sgpc.save()

    # clear and add copied sgps to sgpc_copy
    sgpc.associated_sgprojects.clear()

    for new_sgp in copied_sgps:
        try:
            sgpc.associated_sgprojects.add(new_sgp)
        except ValueError:
            # TODO: - handle error
            continue

    sgpc.save()

    return sgpc


def sgpc_append_editCpa_step(sgpc: SGPC, deletions: dict, additions: dict):
    """
    Appends information of user edits on the cpa-mappings,
    to the provenance record of the sgpc.
    """
    next_step = str(len(sgpc.collection_prov_rec))
    sgpc.collection_prov_rec[next_step] = {}
    sgpc.collection_prov_rec[next_step]["type"] = "editcpa"
    sgpc.collection_prov_rec[next_step]["deletions"] = deletions
    sgpc.collection_prov_rec[next_step]["additions"] = additions

    sgpc.save()


def sgpc_append_schema_step(sgpc: SGPC, deletions: dict, additions: dict):
    """
    Appends information of user edits on the schema (subclass-mappings),
    to the provenance record of the sgpc.
    """
    next_step = str(len(sgpc.collection_prov_rec))
    sgpc.collection_prov_rec[next_step] = {}
    sgpc.collection_prov_rec[next_step]["type"] = "schemarefine"
    sgpc.collection_prov_rec[next_step]["deletions"] = deletions
    sgpc.collection_prov_rec[next_step]["additions"] = additions

    sgpc.save()


def sgpc_edit_cpa(sgpc: SGPC, edits: dict):
    """
    Applies user edits of cpa-mappings so the field
    in the sgpc. Then calls sgpc_append_editCpa_step().
    """
    mapping_copy = sgpc.cpaMappings

    for deletion in edits['deleted']:
        for key in mapping_copy:
            if (deletion['s'] == mapping_copy[key][0] and
                deletion['p'] == mapping_copy[key][2] and
                    deletion['o'] == mapping_copy[key][4]):
                # print("deleting ", mapping_copy[key])
                del mapping_copy[key]
                break
    for key, value in edits['added'].items():
        next_key = get_next_unused_key(mapping_copy)
        # ("NEXT KEY", next_key, " TYPE: ", type(next_key))
        # print("TYPEADD: ", type(addition))
        # print("ADD: ", addition)
        # print("TYPEMAP: ", type(mapping_copy))

        # if you want to find the url for properties please check the below code

        # label_collector.append(value['p'])
        # print("-----------------------------------------------")
        # print("label_collector", label_collector)
        # property_uri = get_wikidata_entities(build_query([label_collector]))
        # print("property_uri", property_uri)

        # add url to cpaMapping
        sgps = sgpc.associated_sgprojects.all()
        for sgp in sgps:
            if value['s'] in sgp.original_table_header.values():
                get_slabel_index = list(sgp.original_table_header.values()).index(value['s'])
                sLabel = sgp.provenanceRecord["0"]["selection"]["child"][str(get_slabel_index)]
                sUrl = sgp.provenanceRecord["0"]["selection"]["mapping"][str(get_slabel_index)]

            if value['o'] in sgp.original_table_header.values():
                get_olabel_index = list(sgp.original_table_header.values()).index(value['o'])
                oLabel = sgp.provenanceRecord["0"]["selection"]["child"][str(get_olabel_index)]
                oUrl = sgp.provenanceRecord["0"]["selection"]["mapping"][str(get_olabel_index)]

        # check if property url already present in IKNOWproperty model
        pUrl = get_property_url_by_label(value['p'])

        if pUrl == None:
            pUrl = f"https://planthub.idiv.de/iknow/wiki/P{str(sgpc.id)}_{str(next_key)}"

        mapping_copy[next_key] = [sUrl, sLabel, pUrl, value['p'], oUrl, oLabel]

    sgpc.cpaMappings = mapping_copy
    sgpc_append_editCpa_step(sgpc, deletions=edits['deleted'], additions=edits['added'])

    for sgp in sgpc.associated_sgprojects.all():
        sgp_append_cpa_step(sgp)

    sgpc.save()


def sgpc_edit_schema(sgpc: SGPC, sgpc_pk, edits: dict):
    """
    Applies user edits of schema (subclass-mappings) so the field
    in the sgpc. Then calls sgpc_append_schema_step().
    """
    schemaCopy = sgpc.subclassMappings
    classUrl = "https://planthub.idiv.de/iknow/wiki/C"

    for deletion in edits['deleted']:
        for key, valueDic in schemaCopy.items():
            if (deletion['s'] == valueDic['s'] and
                    deletion['o'] == valueDic['o']):
                print("Deleted: ", schemaCopy[key])
                del schemaCopy[key]
                break

    for key, value in edits['added'].items():
        next_key = get_next_unused_key(schemaCopy)
        schemaCopy[next_key] = {}
        schemaCopy[next_key]['s'] = value['s']
        schemaCopy[next_key]['o'] = value['o']
        schemaCopy[next_key]['slabel'] = classUrl + str(sgpc_pk) + str(next_key) + '0'
        schemaCopy[next_key]['olabel'] = classUrl + str(sgpc_pk) + str(next_key) + '1'

        print("Added: ", schemaCopy[next_key])

    sgpc.subclassMappings = schemaCopy
    sgpc_append_schema_step(sgpc, deletions=edits['deleted'], additions=edits['added'])

    for sgp in sgpc.associated_sgprojects.all():
        sgp_append_schema_step(sgp)

    sgpc.save()


# DOUBLE fix this later
def get_next_unused_key(somedic: dict):
    for i in range(10000):
        if str(i) in somedic:
            i += 1
        else:
            return str(i)

    return False
