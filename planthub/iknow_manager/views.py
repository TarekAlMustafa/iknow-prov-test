import json
import os

from django.http import HttpResponse, JsonResponse
# from iknow_tools.views import get_all_tools_workflow_info
from rest_framework.response import Response
# from distutils.log import error
# from django.db import models
# from django.shortcuts import render
from rest_framework.views import APIView

from planthub.iknow_datasets.models import Dataset
from planthub.iknow_datasets.views import create_filefield, handle_uploaded_file
from planthub.iknow_sgp.models import SGP
from planthub.iknow_sgp.views import (
    append_linking_step,
    create_sgp,
    get_latest_dataset,
    sgp_from_key,
)
from planthub.iknow_sgpc.models import SGPC
from planthub.iknow_sgpc.views import (
    createCollection,
    get_all_projects_name,
    get_all_sgp_info,
    get_all_sgpc_info,
    sgpc_from_key,
)

from .cleaning_scripts import wikitesttool
# from .pdutil.pdconverter import append_boolean_list
from .pdutil.pdreader import (  # get_json_from_csv,; get_list_from_csv,
    get_list_from_csv_first10rows,
)

# from copyreg import constructor

jr_error = JsonResponse({"msg": "error"})

# everything about REQUEST HANDLING in django
# https://docs.djangoproject.com/en/4.0/ref/request-response/

# response error codes ... response codes für django rest_framework nachschauen und dann benutzen
# redirect ... goto und siehe svelte
# tool init


# TODO:
#   - implement testcontainers to run (cleaning/linking)
#   - reading and returning data of linking results (just as cleaningresult for now)
#   - implement rdf-ization for cleaned table data
#   - implement rdf-ization for linked table data
#   - undo functionality (just senseful naming of steps as a dropdown)

#   - check validity of each applied action
#   - return appropriate error codes for specific failures
#   - error handling etc. when client uploads files


class CreateCollectionView(APIView):
    def post(self, request):
        return createCollection(request)


class UploadToCollectionView(APIView):
    def post(self, request):
        """
        Client uploads datasets after Collection creation.
        Load sgpc, then per dataset:
            - handle uploaded file
            - create sgp
            - add file to sgp
        """
        sgpc_pk = request.POST.get('sgpc_pk', default=None)
        sgpc = sgpc_from_key(sgpc_pk)

        if sgpc is False:
            return jr_error

        # iterate over the files in the request
        for key, file in request.FILES.items():
            filename = request.FILES[key].name

            # create sgp and handle file
            new_dataset = handle_uploaded_file(request.FILES[key], filename)
            new_sgp = create_sgp(sgpc.bioprojectname)
            new_sgp.source_dataset.add(new_dataset)
            sgpc.associated_sgprojects.add(new_sgp)

            # print("created new sgp with id: ", new_sgp.id)
            # print("adding sgp to sgpc: ", sgpc.pk)

        return JsonResponse({"msg": "success"})


class FetchDataView(APIView):
    def get(self, request):
        """
        Client fetches latest datasets from a sgpc.
        """
        # get parameters from request
        sgpc_pk = request.GET.get('sgpc_pk', default=None)
        sgpc = sgpc_from_key(sgpc_pk)

        if sgpc is False:
            return jr_error

        # requires filenames, requires dataset content
        req_names = (request.GET.get('names', '') != '')
        req_datasets = (request.GET.get('datasets', '') != '')

        data = self.prepare_datasets(sgpc, req_names, req_datasets)

        # print("returning prepared datasets: ", prepared_datasets)
        response = JsonResponse(data, safe=False)

        return response

    def prepare_datasets(self, sgpc: SGPC, req_names: bool, req_datasets: bool):
        """
        Load and return content and required information on all
        datasets in a sgpc.
        """
        prepared_datasets = {}

        for i, sgp in enumerate(sgpc.associated_sgprojects.all()):
            # print("sgp.id: ", sgp.id, " sgp.bioprojectname: ", sgp.bioprojectname)
            dataset = get_latest_dataset(sgp)
            helper = {}
            helper["sgp_pk"] = sgp.pk

            if req_names:
                helper["filename"] = os.path.basename(dataset.file_field.name)
            if req_datasets:
                helper["dataset"] = get_list_from_csv_first10rows(dataset.file_field.path)

            prepared_datasets[i] = helper

        return prepared_datasets


class DatasetInit(APIView):
    def post(self, request):
        """
        Client selects types and annotations per column.
        Save selection to each sgp.
        """
        data = json.loads(request.body)["requestdata"]

        sgpc_pk = data["sgpc_pk"]
        sgpc = sgpc_from_key(sgpc_pk)

        if sgpc is False:
            return jr_error

        # loops spg's and matches the request data
        # TODO: - change to more safe and elegant (this is very ugly)
        for sgp in sgpc.associated_sgprojects.all():
            for key in data["tabledata"].keys():
                if data["tabledata"][key]["sgp_pk"] == sgp.pk:
                    if len(sgp.provenanceRecord) == 0:
                        self.safe_init_step(sgp, data["tabledata"][key])
                    else:
                        print("Error, trying to apply init phase to provenance record that is not empty.")

        response = JsonResponse({"success": "succesfully initialized"})

        return response

    def safe_init_step(self, sgp: SGP, data):
        sgp.provenanceRecord[0] = {}
        sgp.provenanceRecord[0]["type"] = "init"
        sgp.provenanceRecord[0]["selection"] = data["selection"]

        sgp.save()


class CleaningView(APIView):
    def post(self, request):
        json_data: dict = json.loads(request.body)["requestdata"]
        if "sgpc_pk" not in json_data.keys():
            return jr_error

        # temp_datasets = []

        # # code runs AFTER CLEANING
        # for i, key in enumerate(json_data["actions"]):
        #     # chosen cleaning method, (..= -1 means none)
        #     method = json_data['actions'][key]['method']

        return Response()


# use custom response class to override HttpResponse.close()
class LinkingtoolsResponse(HttpResponse):

    PROCESS_DATA = []

    def close(self):
        super(LinkingtoolsResponse, self).close()
        # last codepoint in request handling
        if self.status_code == 200:
            for i, job in enumerate(self.PROCESS_DATA):
                # assign necessary information
                selections = job[0].provenanceRecord['0']['selection']
                input_file_path = job[1].file_field.path
                output_path = job[2].file_field.path
                method = job[3]

                # starting routine for a tool (like wikitesttool)
                # TODO:
                #   - own function, cased on method
                print(f"Running Job with method: {method} for file: {input_file_path}.")
                col_types = []
                for x in range(len(selections['type'].keys())):
                    try:
                        col_types.append(selections['type'][str(x)])
                    except (Exception):
                        print(f"Error: Key not were its supposed to be in prov rec {job[0].pk} ")
                        return

                # RUNS QUERY ONLY FOR String-type columns!!!
                wikitesttool.main(
                    INPUT_FILE=input_file_path,
                    OUTPUT_FILE=output_path,
                    COL_TYPES=col_types)


class LinkingView(APIView):
    def post(self, request):
        """
        View for invoking a linking tool. Client sends
        a choice for each sgp + dataset in a sgpc.
        Starting the tool is handled in the LinkingtoolsResponse.
        """
        json_data = json.loads(request.body)["requestdata"]

        # check if the desired key is there
        if "sgpc_pk" not in json_data.keys():
            return jr_error

        response = LinkingtoolsResponse()

        # one job for each sgp
        # contains info about tools, and datasets
        jobs = []

        # for every chosen action prepare a job
        for i, key in enumerate(json_data["actions"]):
            # chosen cleaning method, (..= -1 means none)
            method = json_data['actions'][key]['method']

            sgp, latest_dataset, output_file = self.prepare_job(key)

            if sgp:
                jobs.append([sgp, latest_dataset, output_file, method])
            else:
                return jr_error

            # write to provenance record
            append_linking_step(sgp, method, latest_dataset.pk, output_file.pk)

        # assign jobs to response to handle
        # tool execution after returning the response to the client
        response.PROCESS_DATA = jobs

        return response

    def prepare_job(self, key):
        """
        Load sgp from the given key. Load the latest dataset entry.
        Create a new output FileField and return everything.
        """
        sgp = sgp_from_key(key)
        latest_dataset: Dataset = get_latest_dataset(sgp)
        output_file = create_filefield(
            self.suffix_filename_with_sgp(sgp, os.path.basename(latest_dataset.file_field.name)))

        # one job each with all necessary information
        return sgp, latest_dataset, output_file

    def suffix_filename_with_sgp(self, sgp, filename: str):
        """
        Creates a unique filename based on sgp key and length
        of the provenance record. [Change this later!]
        """
        return f"{sgp.pk}_{len(sgp.provenanceRecord)}_{filename}"


class SGPInfoView(APIView):
    def get(self, request):
        response = JsonResponse({"tabledata": get_all_sgp_info()})
        return response


class SGPCInfoView(APIView):
    def get(self, request):
        response = JsonResponse({"tabledata": get_all_sgpc_info()})
        return response


class ProjectNamesView(APIView):
    def get(self, request):
        response = JsonResponse({"projectNames": get_all_projects_name()})
        return response
