from django.core.exceptions import ObjectDoesNotExist
from django.http import JsonResponse

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


def get_all_sgp_info():
    """
    Returns information about all sgp in the database,
    for the client to display and choose from.
    """
    info = [['Collectionname', 'Bioprojectname', 'Source dataset']]
    for sgpc in SGPC.objects.all():
        for sgp in sgpc.associated_sgprojects.all():
            info.append([sgpc.collectionname, sgp.bioprojectname, sgp.source_dataset.all()[0].file_field.name])

    return info


def get_all_sgpc_info():
    """
    Returns information about all sgpc in the database,
    for the client to display and choose from.
    """
    info = [['Collectionname', 'Bioprojectname', '# associated graphs']]

    for sgpc in SGPC.objects.all():
        info.append([sgpc.collectionname, sgpc.bioprojectname, len(sgpc.associated_sgprojects.all())])

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
