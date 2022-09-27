# THis file is saving information about a SGPC.

from django.core.exceptions import ObjectDoesNotExist
from django.http import JsonResponse

from planthub.iknow_sgp.models import SGP
from planthub.iknow_sgp.views import (
    append_editCpa_step,
    append_schemaRefine_step,
    get_header_mapping,
    get_original_header,
    is_in_progress,
    replace_mapping_file_with_copy,
)

from .models import SGPC, BioProject

# from .serializer import CreateCollectionSerializer

# creates entry in SGPC
# expects a dict in data with 'data' : {..} and optional subkeys:
# bioprojectname, collectionname, description
# everything else will be ignored or results in error message and nothing happening


# TODO: - rewrite this with foreign key and or serializer!
def createCollection(request):
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
    if data['data']['projectChoice'] == 'select':
        for proj in BioProject.objects.all():
            if proj.name == choice:
                new_collection = SGPC()
                new_collection.bioprojectname = proj.name
                new_collection.save()
                return JsonResponse({"project_id": new_collection.pk})
    # client wants to create a new project
    elif data['data']['projectChoice'] == 'create':
        if not BioProject.name_exists(choice):
            newProject = BioProject()
            newProject.name = choice
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


def get_all_sgpc_info():
    """
    Returns information about all sgpc in the database,
    for the client to display and choose from.
    """
    info = [['Collectionname', 'Bioprojectname', '# associated graphs']]
    # test = {0:5, 1:3, 4:5}
    sgpc: SGPC
    for sgpc in SGPC.objects.all():
        # len(sgpc.associated_sgprojects.all()) <-- this is extremely slow, (never use this if possible)
        info.append([sgpc.collectionname, sgpc.bioprojectname, sgpc.associated_sgprojects.all().count(), sgpc.pk])
        # info.append([0, 0, 0])
        # info.append([0, 0, len(sgpc.associated_sgprojects.all())])  # 0.7-1.4 s
        # info.append([0, sgpc.bioprojectname, 0])    # 0.02-0.1 s
        # info.append([sgpc.collectionname, 0, 0])    # 0.02-0.1 s
        # info.append([0, 0, len(test)])

    return info


def get_all_projects_name():
    """
    Returns information about all Bioprojects in the database,
    for the client to display and choose from.
    """

    info = [['--select one--']]

    for proj_name in BioProject.get_all_project_names():
        info.append([proj_name['name']])

    return info


def is_in_progress_sgpc(sgpc: SGPC):
    """
    Checks if tool is running for a given sgpc.
    Calls is_in_progress on each sgp.
    """

    for sgp in sgpc.associated_sgprojects.all():
        if is_in_progress(sgp):
            return True

    # no sgp is still in progress
    return False


def get_all_header_mappings(sgpc: SGPC):
    all_header_mappings = []

    for sgp in sgpc.associated_sgprojects.all():
        original_header = get_original_header(sgp)
        header_mapping = get_header_mapping(sgp)
        for i, entry in enumerate(original_header):
            all_header_mappings.append([entry, header_mapping[i]])

    return all_header_mappings


def get_history_sgpc(sgpc: SGPC):
    sgp0 = sgpc.associated_sgprojects.all()[0]

    helper = []
    for key, phase in sgp0.provenanceRecord.items():
        helper.append([key, phase['type']])

    return helper


def get_history_sgpc_renamed(sgpc: SGPC):
    sgp0 = sgpc.associated_sgprojects.all()[0]

    helper = []
    for key, phase in sgp0.provenanceRecord.items():
        name = ""
        cur_type = phase['type']

        if cur_type == 'linking':
            name = "Cells Linking"
        if cur_type == 'cleaning':
            name = "Cleaning"
        if cur_type == 'init':
            name = "Column type selection"
        if cur_type == 'editcpa':
            name = "Property declaration"
        if cur_type == 'editmapping':
            name = "Cells Linking (after editing)"
        if cur_type == 'schemarefine':
            name = "Schema Refinement"

        helper.append([key, name])

    return helper


def undo_collection_till_phase(sgpc: SGPC, phase_number: int):
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


def copy_collection(sgpc: SGPC):
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
            replace_mapping_file_with_copy(sgp)
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
    next_step = str(len(sgpc.collection_prov_rec))
    sgpc.collection_prov_rec[next_step] = {}
    sgpc.collection_prov_rec[next_step]["type"] = "editcpa"
    sgpc.collection_prov_rec[next_step]["deletions"] = deletions
    sgpc.collection_prov_rec[next_step]["additions"] = additions

    sgpc.save()


def sgpc_append_schemaRefine_step(sgpc: SGPC, deletions: dict, additions: dict):
    next_step = str(len(sgpc.collection_prov_rec))
    sgpc.collection_prov_rec[next_step] = {}
    sgpc.collection_prov_rec[next_step]["type"] = "schemarefine"
    sgpc.collection_prov_rec[next_step]["deletions"] = deletions
    sgpc.collection_prov_rec[next_step]["additions"] = additions

    sgpc.save()


def edit_cpa_mappings(sgpc: SGPC, edits: dict):
    mapping_copy = sgpc.cpaMappings
    # header_mappings = get_all_header_mappings(sgpc)

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
        print("NEXT KEY", next_key, " TYPE: ", type(next_key))
        # print("TYPEADD: ", type(addition))
        # print("ADD: ", addition)
        print("TYPEMAP: ", type(mapping_copy))

        mapping_copy[next_key] = [value['s'], "", value['p'], "", value['o'], ""]

    sgpc.cpaMappings = mapping_copy
    sgpc_append_editCpa_step(sgpc, deletions=edits['deleted'], additions=edits['added'])

    for sgp in sgpc.associated_sgprojects.all():
        append_editCpa_step(sgp)

    sgpc.save()


def edit_schema(sgpc: SGPC, edits: dict):
    schemaCopy = sgpc.subclassMappings
    # print(mapping_copy)

    for deletion in edits['deleted']:
        for key, valueDic in schemaCopy.items():
            if (deletion['s'] == valueDic['s'] and
                    deletion['o'] == valueDic['o']):
                print("Deleted: ", schemaCopy[key])
                del schemaCopy[key]
                break

    for key, value in edits['added'].items():
        next_key = get_next_unused_key(schemaCopy)
        # print("NEXT KEY", next_key, " TYPE: ", type(next_key))
        # print("TYPEADD: ", type(addition))
        # print("ADD: ", addition)

        schemaCopy[next_key] = {}
        schemaCopy[next_key]['s'] = value['s']
        schemaCopy[next_key]['o'] = value['o']

        print("Added: ", schemaCopy[next_key])

    sgpc.subclassMappings = schemaCopy
    sgpc_append_schemaRefine_step(sgpc, deletions=edits['deleted'], additions=edits['added'])

    for sgp in sgpc.associated_sgprojects.all():
        append_schemaRefine_step(sgp)

    sgpc.save()


# DOUBLE fix this later
def get_next_unused_key(somedic: dict):
    for i in range(10000):
        if str(i) in somedic:
            i += 1
        else:
            return str(i)

    return False
