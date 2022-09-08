from django.core.exceptions import ObjectDoesNotExist
from django.http import JsonResponse

from planthub.iknow_sgp.models import SGP
from planthub.iknow_sgp.views import (
    get_header_mapping,
    get_original_header,
    is_in_progress,
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


# TODO: reduce query amount here (very slow functions)
def get_all_sgp_info():
    """
    Returns information about all sgp in the database,
    for the client to display and choose from.
    """
    info = [['Collectionname', 'Bioprojectname', 'Source dataset']]
    # for sgpc in SGPC.objects.all():
    #     for sgp in sgpc.associated_sgprojects.all():
    #         info.append([sgpc.collectionname, sgp.bioprojectname, sgp.source_dataset.all()[0].file_field.name])
    #         info.append([sgpc.collectionname, sgp.bioprojectname, sgp.original_filename])

    for sgp in SGP.objects.all():
        info.append([sgp.bioprojectname, sgp.bioprojectname, sgp.original_filename])

    return info


def get_all_sgpc_info():
    """
    Returns information about all sgpc in the database,
    for the client to display and choose from.
    """
    info = [['Collectionname', 'Bioprojectname', '# associated graphs']]
    # test = {0:5, 1:3, 4:5}
    for sgpc in SGPC.objects.all():
        # len(sgpc.associated_sgprojects.all()) <-- this is extremely slow, (never use this if possible)
        info.append([sgpc.collectionname, sgpc.bioprojectname, 30, sgpc.pk])
        # info.append([0, 0, 0])
        # info.append([0, 0, len(sgpc.associated_sgprojects.all())])  # 0.7-1.4 s
        # info.append([0, sgpc.bioprojectname, 0])    # 0.02-0.1 s
        # info.append([sgpc.collectionname, 0, 0])    # 0.02-0.1 s
        # info.append([0, 0, len(test)])

    return info


def get_single_sgpc_info(sgpc_pk):
    sgpc = sgpc_from_key(sgpc_pk)
    if sgpc is False:
        return False

    info = [['Bioprojectname', 'Original Filename', "Sgp_pk"]]

    for sgp in sgpc.associated_sgprojects.all():
        info.append([sgp.bioprojectname, sgp.original_filename, sgp.pk])

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
