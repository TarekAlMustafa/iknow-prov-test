from django.http import JsonResponse

from .models import SGPC, BioProject

# from .serializer import CreateCollectionSerializer

# creates entry in SGPC
# expects a dict in data with 'data' : {..} and optional subkeys:
# bioprojectname, collectionname, description
# everything else will be ignored or results in error message and nothing happening


def createCollection(request):
    data: dict = request.data

    # TODO: - rewrite this with foreign key and or serializer!
    if type(data) == dict and 'data' in data.keys():
        choice = data['data']['bioprojectname']

        if data['data']['projectChoice'] == 'select':
            for proj in BioProject.objects.all():
                if proj.name == choice:
                    new_collection = SGPC()
                    new_collection.bioprojectname = proj.name
                    new_collection.save()
                    return JsonResponse({"project_id": new_collection.pk})
        elif data['data']['projectChoice'] == 'create':
            if not BioProject.name_exists(choice):
                newProject = BioProject()
                newProject.name = choice
                newProject.save()

            new_collection = SGPC()
            new_collection.bioprojectname = choice
            new_collection.save()

            return JsonResponse({"project_id": new_collection.pk})


def get_all_sgp_info():
    info = [['Collectionname', 'Bioprojectname', 'Source dataset']]
    for sgpc in SGPC.objects.all():
        for sgp in sgpc.associated_sgprojects.all():
            info.append([sgpc.collectionname, sgp.bioprojectname, sgp.source_dataset.all()[0].file_field.name])

    return info


def get_all_sgpc_info():
    info = [['Collectionname', 'Bioprojectname', '# associated graphs']]

    for sgpc in SGPC.objects.all():
        info.append([sgpc.collectionname, sgpc.bioprojectname, len(sgpc.associated_sgprojects.all())])

    return info


def get_all_projects_name():
    info = [['--select one--']]

    for proj_name in BioProject.get_all_project_names():
        info.append([proj_name['name']])

    # for name_dic in SGPC.objects.values('bioprojectname').distinct():
    #     info.append([name_dic['bioprojectname']])

    return info
