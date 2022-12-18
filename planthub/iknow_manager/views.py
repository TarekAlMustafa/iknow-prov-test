import json
from datetime import date

import pandas as pd
import requests
from django.conf import settings
# from django.contrib.auth.decorators import login_required
# from rest_framework import permissions
from django.http import HttpResponse, JsonResponse
from rdflib import Graph, Literal, Namespace, URIRef
from rdflib.namespace import OWL, RDF, RDFS
from rest_framework.decorators import api_view
# from django.utils.decorators import method_decorator
# from iknow_tools.views import get_all_tools_workflow_info
from rest_framework.response import Response
# from distutils.log import error
# from django.db import models
# from django.shortcuts import render
from rest_framework.views import APIView

from planthub.iknow_datasets.models import Dataset
from planthub.iknow_datasets.views import create_filefield, handle_uploaded_file
from planthub.iknow_manager.models import (
    CPAmapping,
    IknowEntity,
    create_new_headerclass,
    get_all_headerclasses,
    get_property_url_by_label,
    safe_querymetadata,
    save_cpamappings,
    save_iknow_class,
    save_iknow_property,
)
from planthub.iknow_sgp.models import SGP
from planthub.iknow_sgp.views import (
    sgp_append_cpa_step,
    sgp_append_downloading_step,
    sgp_append_init_step,
    sgp_append_linking_step,
    sgp_append_mapping_step,
    sgp_append_querybuilding_step,
    sgp_append_schema_step,
    sgp_create,
    sgp_edit_mapping,
    sgp_from_key,
    sgp_get_col_types,
    sgp_get_input_file,
    sgp_get_mapping_file,
    sgp_get_output_file,
    sgp_get_provrec,
    sgp_replace_mapping_file_with_copy,
    sgp_replace_source_dataset,
    sgp_set_phase_state,
    sgp_undo_till_linking,
)
from planthub.iknow_sgpc.models import SGPC, BioProject
from planthub.iknow_sgpc.views import (  # get_all_header_mappings,; get_history_sgpc,
    sgpc_copy,
    sgpc_create,
    sgpc_edit_cpa,
    sgpc_edit_schema,
    sgpc_from_key,
    sgpc_history_renamed,
    sgpc_in_progress,
    sgpc_info,
    sgpc_info_by_collection_name,
    sgpc_undo_till_phase,
)

from .cleaning_scripts import findsubclasses, wikitesttool
# from .pdutil.pdconverter import append_boolean_list
from .pdutil.pdreader import (  # get_json_from_csv,; get_list_from_csv,
    get_list_from_csv_first10rows,
)

# import time

IKNOW_NAMESPACE = "https://planthub.idiv.de/iknow/wiki/"

jr_error = JsonResponse({"msg": "error"})
jr_error_message = {"msg": "error"}


# everything about REQUEST HANDLING in django
# https://docs.djangoproject.com/en/4.0/ref/request-response/

# TODO:

#   - check validity of each applied action
#   - return appropriate error codes for specific failures
#   - error handling etc. when client uploads files


class CreateSgpcView(APIView):
    # login required class decorator
    # @method_decorator(login_required)
    # permission_classes = [permissions.IsAuthenticated, ]

    def post(self, request):
        return sgpc_create(request)


class UploadToSgpcView(APIView):
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

        id_counter = 0

        # iterate over the files in the request
        for key, file in request.FILES.items():
            filename = request.FILES[key].name

            # create sgp and handle file
            new_dataset = handle_uploaded_file(request.FILES[key], filename)
            new_sgp = sgp_create()
            new_sgp.source_dataset.add(new_dataset)
            new_sgp.original_filename = filename
            sgpc.associated_sgprojects.add(new_sgp)

            header = self.get_dataset_header(new_dataset.file_field.path)
            new_sgp.original_table_header = header

            new_sgp.id_in_collection = id_counter
            new_sgp.save()
            # print("created new sgp with id: ", new_sgp.id)
            # print("adding sgp to sgpc: ", sgpc.pk)

            id_counter += 1

        return JsonResponse({"msg": "success"})

    def get_dataset_header(self, filepath):
        df = pd.read_csv(filepath)
        header = list(df.head())

        dic_header = {}
        for i, entry in enumerate(header):
            dic_header[str(i)] = entry

        return dic_header


class FetchDataView(APIView):
    def get(self, request):
        """
        Client fetches latest datasets from a sgpc.
        (required) fetching query parameters:
        @ req_names         -> filenames
        @ req_datasets      -> current output file or linking result
        @ req_history       -> sgpc history
        @ req_type          -> phase type
        @ req_categories    -> header classes
        """
        # get parameters from request
        sgpc_pk = request.GET.get('sgpc_pk', default=None)
        sgpc = sgpc_from_key(sgpc_pk)

        if sgpc is False:
            return jr_error

        if sgpc_in_progress(sgpc):
            print("Error in FetchDataView: sgpc ", sgpc.pk, " is still running.")
            return jr_error

        # requires filenames, requires dataset content
        req_names = (request.GET.get('names', '') != '')
        req_datasets = (request.GET.get('datasets', '') != '')
        req_history = (request.GET.get('history', '') != '')
        req_type = request.GET.get('type', '')
        req_categories = (request.GET.get('categories', '') != '')

        if req_type == "cleaning":
            data = self.prepare_datasets(sgpc, req_names, req_datasets, req_history, req_categories)
        if req_type == "linking":
            data = self.prepare_linking_result(sgpc, req_names, req_datasets, req_history)
        else:
            data = self.prepare_datasets(sgpc, req_names, req_datasets, req_history, req_categories)

        # print("data", data)

        response = JsonResponse(data, safe=False)

        return response

    def prepare_linking_result(self, sgpc: SGPC, req_names: bool, req_datasets: bool, req_history: bool):
        """
        Load and return content and required information on all
        datasets in a sgpc.
        """
        prepared_datasets = {}
        response_data = {}

        for i, sgp in enumerate(sgpc.associated_sgprojects.all()):
            # print("sgp.id: ", sgp.id, " sgp.bioprojectname: ", sgp.bioprojectname)
            helper = {}
            helper["sgp_pk"] = sgp.pk

            if req_names:
                helper["filename"] = sgp.original_filename

            helper["dataset"] = self.load_unique_mappings(sgp)

            prepared_datasets[i] = helper

        if req_history:
            response_data["history"] = sgpc_history_renamed(sgpc)
        response_data["tabledata"] = prepared_datasets

        return response_data

    def load_unique_mappings(self, sgp):
        """
        Searches for unique mappings of the mapping file
        of the sgp, and combines it with their original
        cell values for display in frontend.
        """
        input_dataset = sgp_get_input_file(sgp)
        mapping_dataset = sgp_get_mapping_file(sgp)

        if input_dataset is False or mapping_dataset is False:
            return jr_error_message

        input_df = pd.read_csv(input_dataset.file_field.path)
        mapping_dataset = pd.read_csv(mapping_dataset.file_field.path)

        col_types = sgp_get_col_types(sgp, binary=True)

        all_mappings = {}

        # load each column separately (that's how they are displayed in frontend)
        for i, col_name in enumerate(input_df):
            if col_types[i]:
                col_mappings = self.load_unique_col_mappings(input_df[col_name], mapping_dataset[col_name], col_name)
                all_mappings[str(i)] = col_mappings

        return all_mappings

    def load_unique_col_mappings(self, col, result_col, col_name):
        """
        Loads unique mappings of given column.
        """
        already_seen = []
        mappings = [[col_name, f"{col_name} links"]]

        for i, cell_value in enumerate(col):
            if cell_value not in already_seen:
                already_seen.append(cell_value)
                mappings.append([cell_value, str(result_col[i])])

        return mappings

    def prepare_datasets(self, sgpc: SGPC, req_names: bool, req_datasets: bool,
                         req_history: bool, req_categories: bool):
        """
        Load and return content and required information on all
        datasets in a sgpc.
        """

        # TODO task 2
        #
        prepared_datasets = {}
        response_data = {}

        for i, sgp in enumerate(sgpc.associated_sgprojects.all()):
            # print("sgp.id: ", sgp.id, " sgp.bioprojectname: ", sgp.bioprojectname)
            dataset = sgp_get_output_file(sgp)
            helper = {}
            helper["sgp_pk"] = sgp.pk

            if req_names:
                helper["filename"] = sgp.original_filename
            if req_datasets:
                helper["dataset"] = get_list_from_csv_first10rows(dataset.file_field.path)

            prepared_datasets[i] = helper

        if req_history:
            response_data["history"] = sgpc_history_renamed(sgpc)

        if req_categories:
            response_data["categories"] = get_all_headerclasses()

        response_data["tabledata"] = prepared_datasets

        return response_data


class ColumntypesView(APIView):
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

        sgps = sgpc.associated_sgprojects.all()

        for sgp in sgps:
            if len(sgp.provenanceRecord) > 0:
                # trying to apply init phase to provenance record that is not empty
                return jr_error

        # loops spg's and matches the request data
        sgp: SGP
        for sgp in sgps:
            for key in data["tabledata"].keys():
                if data["tabledata"][key]["sgp_pk"] == sgp.pk:
                    # this executes ones per sgp in the sgpc
                    self.check_for_created_categories(data["tabledata"][key]["created"],
                                                      data["tabledata"][key]["selection"])

                    sgp_append_init_step(sgp, data["tabledata"][key]["selection"])

        response = JsonResponse({"success": "succesfully initialized"})

        return response

    def check_for_created_categories(self, created, selection):
        """
        Creates new header classes based on user inputs. Adds
        newly created classes to the selection data.
        """

        # TODO: - Validate user entry here
        #       - shouldnt be empty and should be valid url

        new_categories = {}
        for key, value in created["newsuburi"].items():
            if key in created["newmainuri"]:
                create_new_headerclass({
                    "newsuburi": value,
                    "newsublabel": created["newsublabel"][key],
                    "newmainuri": created["newmainuri"][key],
                    "newmainlabel": created["newmainlabel"][key]
                })
            else:
                create_new_headerclass({
                    "newsuburi": value,
                    "newsublabel": created["newsublabel"][key],
                    "newmainlabel": selection["parent"][key]
                })

        # add created to selection
        for key in created["newmainlabel"]:
            selection["parent"][key] = created["newmainlabel"][key]
            selection["child"][key] = created["newsublabel"][key]
            selection["mapping"][key] = created["newsuburi"][key]

        for key in created["newsublabel"]:
            if key in new_categories:
                continue
            else:
                selection["child"][key] = created["newsublabel"][key]
                selection["mapping"][key] = created["newsuburi"][key]


class CleaningView(APIView):
    def post(self, request):
        json_data: dict = json.loads(request.body)["requestdata"]
        if "sgpc_pk" not in json_data.keys():
            return jr_error

        # TODO: implement analog to LinkingView and LinkingToolsResponse
        # TODO task 3: write cleaning function here

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
                input_file_path = job[1].file_field.path
                output_path = job[2].file_field.path
                method = job[3]

                # starting routine for a tool (like wikitesttool)
                # TODO:
                #   - own function, cased on method
                print(f"Running Job with method: {method} for file: {input_file_path}.")
                col_types = sgp_get_col_types(job[0])

                # RUNS QUERY ONLY FOR String-type columns!!!
                wikitesttool.main(
                    INPUT_FILE=input_file_path,
                    OUTPUT_FILE=output_path,
                    COL_TYPES=col_types)

                sgp_set_phase_state(job[0], "done")


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
            sgp_append_linking_step(sgp, latest_dataset.pk, output_file.pk, "Direct API")

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
        latest_dataset: Dataset = sgp_get_output_file(sgp)
        output_file = create_filefield(
            self.suffix_filename_with_sgp(sgp, "output.csv"))

        # one job each with all necessary information
        return sgp, latest_dataset, output_file

    def suffix_filename_with_sgp(self, sgp, filename: str):
        """
        Creates a unique filename based on sgp key and length
        of the provenance record. [Change this later!]
        """
        return f"{sgp.pk}_{len(sgp.provenanceRecord)}_{filename}"


class FetchSubclassesView(APIView):
    def get(self, request):
        """
        Returns subclass-mappings. If sgpc.subclassMappings is empty,
        tries to generate them from the database.
        """
        # get parameters from request
        sgpc_pk = request.GET.get('sgpc_pk', default=None)
        sgpc = sgpc_from_key(sgpc_pk)

        if sgpc is False:
            return jr_error

        all_subclasses = {'sgpc_pk': sgpc_pk}

        if (len(sgpc.subclassMappings) == 0):
            find_subclasses(sgpc)

        all_subclasses['mappings'] = sgpc.subclassMappings
        all_subclasses['history'] = sgpc_history_renamed(sgpc)

        response = JsonResponse(all_subclasses)

        return response


class FetchCpaView(APIView):
    def get(self, request):
        """
        Returns cpa-mappings. If sgpc.cpaMappings is empty,
        tries to generate them from the database.
        """
        # get parameters from request
        sgpc_pk = request.GET.get('sgpc_pk', default=None)
        sgpc = sgpc_from_key(sgpc_pk)

        if sgpc is False:
            return jr_error

        all_mappings = {'sgpc_pk': sgpc_pk}

        if (len(sgpc.cpaMappings) == 0):
            find_mappings(sgpc)

        all_mappings["mappings"] = sgpc.cpaMappings
        all_mappings["header"] = self.get_all_original_headers(sgpc)
        all_mappings["history"] = sgpc_history_renamed(sgpc)

        response = JsonResponse(all_mappings)

        return response

    def header_json_to_list(self, json_header):
        """
        Helper method to reformat JSON entries from the database
        into a list.
        """
        helper = []
        for key in json_header:
            helper.append(json_header[key])
        return helper

    def get_all_original_headers(self, sgpc: SGPC):
        """
        Gets all original headers from SGPs in a SGPC and
        returns them as a list in a proper format.
        """
        header = []
        for i, sgp in enumerate(sgpc.associated_sgprojects.all()):
            header += self.header_json_to_list(sgp.original_table_header)

        return header


class EditMappingsView(APIView):
    def post(self, request):
        # get parameters from request
        data = json.loads(request.body)["requestdata"]

        sgpc_pk = data['sgpc_pk']
        sgpc = sgpc_from_key(sgpc_pk)

        if sgpc is False:
            return jr_error

        # TODO: - apply this for all sgp also if edits is empty
        for sgp_number in data['edits']:
            sgp = sgp_from_key(sgp_number)
            if sgp is False:
                return jr_error

            sgp_edit_mapping(sgp, data['edits'][sgp_number])
            sgp_append_mapping_step(sgp, data['edits'][sgp_number])

        return Response()


class EditCpaView(APIView):
    def post(self, request):
        # get parameters from request
        data = json.loads(request.body)["requestdata"]
        # print(data)

        sgpc_pk = data['sgpc_pk']
        sgpc = sgpc_from_key(sgpc_pk)

        if sgpc is False:
            return jr_error

        sgpc_edit_cpa(sgpc, data)
        return Response()


class EditSchemaView(APIView):
    def post(self, request):
        # get parameters from request
        data = json.loads(request.body)["requestdata"]
        # print(data)

        sgpc_pk = data['sgpc_pk']
        sgpc = sgpc_from_key(sgpc_pk)

        if sgpc is False:
            return jr_error

        sgpc_edit_schema(sgpc, sgpc_pk, data)

        return Response()


class UndoSgpcView(APIView):
    def post(self, request):
        data = json.loads(request.body)["data"]
        step = int(data['step'])
        sgpc_pk = data['sgpc_pk']
        sgpc = sgpc_from_key(sgpc_pk)

        if sgpc is False:
            return jr_error
        print("RESETVIEW, Step: ", step, " on sgpc: ", sgpc_pk)

        sgpc_undo_till_phase(sgpc, step)

        return JsonResponse({"phase": "linking"})


class CopySgpcView(APIView):
    def post(self, request):
        """
        Copies a SGPC with all its SGPs. If reset_to_phase is
        given, it also clears all data until the given phase
        number. This gives the client a copied collection to
        work with.
        """
        sgpc_pk = request.GET.get('sgpc_pk', default=None)
        reset_to_phase = request.GET.get('reset', default=None)

        sgpc = sgpc_from_key(sgpc_pk)

        if sgpc is False:
            return jr_error

        new_sgpc = sgpc_copy(sgpc)

        if reset_to_phase is not None:
            sgpc_undo_till_phase(new_sgpc, int(reset_to_phase))

        return Response()


class RerunView(APIView):
    def post(self, request):
        sgpc_pk = request.GET.get('sgpc_pk', default=None)
        sgpc: SGPC = sgpc_from_key(sgpc_pk)

        if sgpc is False:
            return jr_error

        sgp_data = []
        sgp: SGP
        for sgp in sgpc.associated_sgprojects.all():
            sgp_data.append({
                'id_in_collection': sgp.id_in_collection,
                'provrec': sgp.provenanceRecord
            })

        # copy this by value
        old_sgpc_provrec = dict(sgpc.collection_prov_rec)
        rerun_subclasses = False
        if (len(sgpc.subclassMappings) > 0):
            rerun_subclasses = True

        rerun_cpa = False
        if (len(sgpc.cpaMappings) > 0):
            rerun_cpa = True

        new_sgpc = sgpc_copy(sgpc)

        # undo collection up until init
        sgpc_undo_till_phase(new_sgpc, 1)

        self.rerun_sgp(sgp_data, new_sgpc)

        # rerun phases from sgpc provenance record (that includes applying user changes)
        self.rerun_sgpc(new_sgpc, old_sgpc_provrec, rerun_subclasses, rerun_cpa)

        return Response()

    def rerun_sgp(self, sgp_data, new_sgpc: SGPC):
        print("Starting rerun")
        for data in sgp_data:
            new_sgp = new_sgpc.associated_sgprojects.filter(id_in_collection=data['id_in_collection'])[0]

            for key, phase in data['provrec'].items():
                print("Rerunnign phase: ", phase, " for sgp: ", new_sgp.pk)
                if phase['type'] == 'init':
                    # copied for now, but might change later
                    pass
                elif phase['type'] == 'cleaning':
                    # do this later
                    pass
                elif phase['type'] == 'linking':
                    latest_dataset: Dataset = sgp_get_output_file(new_sgp)
                    print("LATEST_DATASET: ", latest_dataset)
                    output_file = create_filefield(
                        self.suffix_filename_with_sgp(new_sgp, "output.csv"))

                    print("OUTPUT_FILE: ", output_file)
                    sgp_append_linking_step(new_sgp, latest_dataset.pk, output_file.pk, "Direct API")
                    self.run_linking_tool(new_sgp, latest_dataset, output_file)

                elif phase['type'] == 'editmapping':
                    if "edits" in phase:
                        sgp_edit_mapping(new_sgp, phase['edits'])
                        sgp_append_mapping_step(new_sgp, phase['edits'])
                    else:
                        sgp_append_mapping_step(new_sgp, {})
                elif phase['type'] == 'editcpa':
                    sgp_append_cpa_step(new_sgp)
                elif phase['type'] == 'schemarefine':
                    sgp_append_schema_step(new_sgp)

    def rerun_sgpc(self, sgpc: SGPC, old_sgpc_provrec: dict, rerun_subclasses, rerun_cpa):
        if rerun_subclasses:
            # TODO: - DRY, move everything after method call into method find_subclasses
            find_subclasses(sgpc)

        if rerun_cpa:
            find_mappings(sgpc)

        for key, phase in old_sgpc_provrec.items():
            if phase['type'] == 'editcpa':
                if "edits" in phase:
                    sgpc_edit_cpa(sgpc, phase['edits'])
                else:
                    sgpc_edit_cpa(sgpc, {'deleted': {}, 'added': {}})
            elif phase['type'] == 'schemarefine':
                if "edits" in phase:
                    sgpc_edit_schema(sgpc, phase['edits'])
                else:
                    sgpc_edit_schema(sgpc, {'deleted': {}, 'added': {}})

    def run_linking_tool(self, sgp, latest_dataset, output_file):
        # assign necessary information
        input_file_path = latest_dataset.file_field.path
        output_path = output_file.file_field.path
        # method = job[3]

        # starting routine for a tool (like wikitesttool)
        # TODO:
        #   - own function, cased on method
        # print(f"Running Job with method: {method} for file: {input_file_path}.")
        col_types = sgp_get_col_types(sgp)

        # RUNS QUERY ONLY FOR String-type columns!!!
        wikitesttool.main(
            INPUT_FILE=input_file_path,
            OUTPUT_FILE=output_path,
            COL_TYPES=col_types)

        sgp_set_phase_state(sgp, "done")

    def suffix_filename_with_sgp(self, sgp, filename: str):
        """
        Creates a unique filename based on sgp key and length
        of the provenance record. [Change this later!]
        """
        return f"{sgp.pk}_{len(sgp.provenanceRecord)}_{filename}"


class ChangeFileAndRerunView(APIView):
    # TODO: - check if new uploaded dataset has the same columns as original one
    def post(self, request):
        sgpc_pk = request.GET.get('sgpc_pk', default=None)
        sgpc = sgpc_from_key(sgpc_pk)

        if sgpc is False:
            return jr_error

        new_sgpc = sgpc_copy(sgpc)
        sgpc_undo_till_phase(new_sgpc, 1)

        old_sgpc = SGPC.objects.get(pk=sgpc_pk)

        for sgp_pk, file in request.FILES.items():
            new_dataset = handle_uploaded_file(file, file.name)

            old_sgp: SGP
            for old_sgp in old_sgpc.associated_sgprojects.all():
                if str(old_sgp.pk) == sgp_pk:

                    new_sgp: SGP
                    for new_sgp in new_sgpc.associated_sgprojects.all():
                        if new_sgp.id_in_collection == old_sgp.id_in_collection:
                            new_sgp.original_filename = file.name
                            print(str(old_sgp.pk), " ", sgp_pk)
                            sgp_replace_source_dataset(new_sgp, new_dataset)

        sgp_data = []
        old_sgp: SGP
        for old_sgp in old_sgpc.associated_sgprojects.all():
            sgp_data.append({
                'id_in_collection': old_sgp.id_in_collection,
                'provrec': old_sgp.provenanceRecord
            })

        self.rerun_sgp_until_linking(sgp_data, new_sgpc)

        return Response()

    def rerun_sgp_until_linking(self, sgp_data, new_sgpc: SGPC):
        print("Starting rerun")
        for data in sgp_data:
            new_sgp: SGP
            new_sgp = new_sgpc.associated_sgprojects.filter(id_in_collection=data['id_in_collection'])[0]
            if new_sgp.datasets_copied:
                # COPY PROVREC
                new_sgp.provenanceRecord = data['provrec']
                sgp_replace_mapping_file_with_copy(new_sgp)
                sgp_undo_till_linking(new_sgp)
                continue

            for key, phase in data['provrec'].items():
                print("Rerunnign phase: ", phase, " for sgp: ", new_sgp.pk)
                if phase['type'] == 'init':
                    # copied for now, but might change later
                    pass
                elif phase['type'] == 'cleaning':
                    # do this later
                    pass
                elif phase['type'] == 'linking':
                    latest_dataset: Dataset = sgp_get_output_file(new_sgp)
                    output_file = create_filefield(
                        self.suffix_filename_with_sgp(new_sgp, "output.csv"))
                    sgp_append_linking_step(new_sgp, latest_dataset.pk, output_file.pk, "Direct API")
                    self.run_linking_tool(new_sgp, latest_dataset, output_file)

    def run_linking_tool(self, sgp, latest_dataset, output_file):
        # assign necessary information
        input_file_path = latest_dataset.file_field.path
        output_path = output_file.file_field.path
        # method = job[3]

        # starting routine for a tool (like wikitesttool)
        # TODO:
        #   - own function, cased on method
        # print(f"Running Job with method: {method} for file: {input_file_path}.")
        col_types = sgp_get_col_types(sgp)

        # RUNS QUERY ONLY FOR String-type columns!!!
        wikitesttool.main(
            INPUT_FILE=input_file_path,
            OUTPUT_FILE=output_path,
            COL_TYPES=col_types)

        sgp_set_phase_state(sgp, "done")

    def suffix_filename_with_sgp(self, sgp, filename: str):
        """
        Creates a unique filename based on sgp key and length
        of the provenance record. [Change this later!]
        """
        return f"{sgp.pk}_{len(sgp.provenanceRecord)}_{filename}"


class DeleteDBView(APIView):
    def post(self, request):
        for o in IknowEntity.objects.all():
            o.delete()

        for d in Dataset.objects.all():
            if d.pk > 760:
                d.delete()

        for sgp in SGP.objects.all():
            if sgp.pk > 573:
                sgp.delete()

        for sgpc in SGPC.objects.all():
            print(sgpc.pk)
            if sgpc.pk > 343:
                sgpc.delete()

        return Response()


# TODO: - save query meta data here when there is the proper request from querybuilding page
class SaveQueryMetadataView(APIView):
    def post(self, request):
        pass


def find_subclasses(sgpc: SGPC):
    """
    Generates subclass-mappings based on data in the collection and
    fetched results from the wikidata endpoint.
    """
    headers = []

    for sgp in sgpc.associated_sgprojects.all():
        col_types = sgp_get_col_types(sgp)
        for i, entry in enumerate(sgp.provenanceRecord['0']['selection']['mapping'].values()):
            # We only create subclass mapping forcolumn with type of STRING
            if col_types[i] == "String":
                label = sgp.provenanceRecord['0']['selection']['child'][str(i)]
                headers.append([label, entry])
            else:
                # TODO: act accordingly
                pass

    result = findsubclasses.main(headers, "")

    counter = 0
    subclasses_to_save = {}
    for s in result:
        for i, parent in enumerate(result[s]['parentclasses']):
            helper = {'s': result[s]['uri'], 'slabel': result[s]['slabel'],
                      'o': parent, 'olabel': result[s]['parentlabel'][i]}
            subclasses_to_save[str(counter)] = helper
            counter += 1

    # this list has duplicated values. to remove duplicated, we do:

    subclasses_to_save_unique = {}

    for key, value in subclasses_to_save.items():
        if value not in subclasses_to_save_unique.values():
            subclasses_to_save_unique[key] = value

    # print ("***** subclasses_to_save NO duplicated", subclasses_to_save_unique)

    sgpc.subclassMappings = subclasses_to_save_unique
    sgpc.save()


def find_mappings(sgpc: SGPC):
    """
    Generates cpa-mappings based on data in the collection and
    the manually inserted CPAmapping database entries.
    """
    # TODO: - make sure duplicated mappings aren't saved
    mappings_helper = {}

    sgp: SGP
    for i, sgp in enumerate(sgpc.associated_sgprojects.all()):
        try:
            col_mappings = sgp.provenanceRecord['0']['selection']['mapping']
        except KeyError:
            print("Could not load init-selection-mappings from sgp: ", sgp.pk)
            # TODO: - handle error
            continue

        key_counter = 0
        for key in col_mappings:
            for triple in CPAmapping.objects.filter(s=col_mappings[key]):
                if triple.o in col_mappings.values():
                    new_entry = [triple.s, triple.sLabel, triple.p,
                                 triple.pLabel, triple.o, triple.oLabel]
                    mappings_helper[key_counter] = new_entry
                    key_counter += 1

    sgpc.cpaMappings = mappings_helper
    sgpc.save()


def generate_missing_entities(sgp: SGP, sgpcID):
    """
    For a given sgp, reads mapping file and latest dataset.
    Searches for IknowEntities with same value, or creates new
    Entities if none found. Replaces NORESULT values in mapping
    file, with EntityUri.
    """

    mapping_file: Dataset = sgp_get_mapping_file(sgp)
    latest_dataset: Dataset = sgp_get_input_file(sgp)
    mapping_df = pd.read_csv(mapping_file.file_field.path)
    original_df = pd.read_csv(latest_dataset.file_field.path)

    col_types = sgp_get_col_types(sgp)

    for i, value in enumerate(mapping_df):
        if col_types[i] == "String":
            for j, cell in enumerate(mapping_df[value]):
                if cell == "NORESULT":

                    # https://docs.djangoproject.com/en/4.1/ref/models/querysets/#get-or-create
                    result = IknowEntity.objects.get_or_create(label=original_df.iat[j, i])
                    entity: IknowEntity = result[0]
                    new = result[1]

                    if new:
                        entity.uri = f"{IKNOW_NAMESPACE}E{sgpcID}_{entity.pk}"
                        entity.label = original_df.iat[j, i]
                        entity.save()

                    mapping_df.iat[j, i] = entity.uri

    mapping_df.to_csv(mapping_file.file_field.path, index=False)

    return Response()


def get_next_unused_key(somedic: dict):
    for i in range(10000):
        if str(i) in somedic:
            i += 1
        else:
            return str(i)

    return False


@api_view(['GET'])
def get_sgpc_info(request):
    """
    Returns list with information about all sgpcs.
    """
    print(" I am in get all-sgpc-info")
    response = JsonResponse({"tabledata": sgpc_info()})

    return response


@api_view(['GET'])
def get_sgpc_info_by_collection_name(request):
    """
    Returns list with information about all sgpcs by collectionname.
    """
    sgpcID = request.GET.get('sgpcID', default=None)

    response = JsonResponse({"tabledata": sgpc_info_by_collection_name(sgpcID)})

    return response


@api_view(['GET'])
def get_sgpc_provenance(request):
    """
    Returns information about all phases in the provenance record
    of all sgps in a sgpc.
    """
    print("I am in get fetch-collection-provenance")
    sgpc_pk = request.GET.get('sgpc_pk', default=None)
    sgpc = sgpc_from_key(sgpc_pk)

    if sgpc is False:
        return jr_error

    createdBy = sgpc.createdBy
    createdAt = sgpc.createdAt

    response_content = {"tabledata": {}, "sgpc_pk": sgpc_pk, "createdBy": createdBy, "createdAt": createdAt}

    sgp: SGP
    for i, sgp in enumerate(sgpc.associated_sgprojects.all()):
        response_content["tabledata"][i] = {}
        response_content["tabledata"][i]["provdata"] = sgp_get_provrec(sgp.pk)
        response_content["tabledata"][i]["sgp_pk"] = sgp.pk
        response_content["tabledata"][i]["filename"] = sgp.original_filename

    response = JsonResponse(response_content)

    return response


@api_view(['GET'])
def download_sgpc_provenance(request):
    """
    Returns information about all phases in the provenance record
    of all sgps in a sgpc.
    """
    sgpc_pk = request.GET.get('sgpc_pk', default=None)
    sgpc = sgpc_from_key(sgpc_pk)

    if sgpc is False:
        return jr_error

    response_content = {"tabledata": {}, "sgpc_pk": sgpc_pk}

    sgp: SGP
    for i, sgp in enumerate(sgpc.associated_sgprojects.all()):
        response_content["tabledata"][i] = {}
        response_content["tabledata"][i]["provdata"] = sgp_get_provrec(sgp.pk)

    response = JsonResponse(response_content)

    return response


@api_view(['GET'])
def get_bioproject_names(request):
    # permission_classes = [permissions.IsAuthenticated, ]  # add this for authentication
    """
    Returns all disctinct bioproject names.
    """
    response = JsonResponse({"projectNames": BioProject.get_all_project_names()})
    return response


@api_view(['GET'])
def get_collection_names(request):
    """
    Returns all disctinct bioproject names.
    """

    # print("get_all_collection_names", SGPC.get_all_collection_names())

    response = JsonResponse({"collectionnames": SGPC.get_all_collection_names()})
    return response


class QueryTemplate(APIView):
    def get(self, request):
        # get parameters from request
        sgpc_pk = request.GET.get('sgpc_pk', default=None)
        print("sgpc_pk2", sgpc_pk)
        sgpc = sgpc_from_key(sgpc_pk)

        if sgpc is False:
            return jr_error

        proj_name = sgpc.bioprojectname
        for sgp in sgpc.associated_sgprojects.all():
            data = sgp.provenanceRecord["0"]["selection"]
            original_header = sgp.original_table_header
            # print("original_header", original_header)
            safe_querymetadata(data, original_header, proj_name)
            sgp_append_querybuilding_step(sgp)

        return Response()


class GenerateTTL(APIView):
    # defining namespace variables
    WIKI = Namespace("https://www.wikidata.org/wiki/")
    IKNOW = Namespace("https://planthub.idiv.de/iknow/wiki/")
    IKNOW_RO = Namespace("https://planthub.idiv.de/iknow/RO")

    # such an index can be used to name URIS/graphnames/etc. accordingly
    row_observation_index = 0

    def add_rowobservation_class(self, g, sgpcID):
        """
        e.g.
        [<https://planthub.idiv.de/iknow/RO>] [a] [owl:Class] ;
                    [rdfs:label] ["Virtual-Row-Observation"] .
        """
        g.add((
            URIRef(f"{self.IKNOW_RO}"),
            RDF.type,
            OWL.Class
        ))

        g.add((
            URIRef(f"{self.IKNOW_RO}"),
            RDFS.label,
            Literal("Virtual Row Observation")
        ))

        g.add((
            URIRef(f"{self.IKNOW_RO}"),
            RDFS.seeAlso,
            Literal("sgpc_" + sgpcID)
        ))

    def get_entites_uri(self, g, label=""):
        # print("label", label)
        # wiki url
        wiki_url = "https://www.wikidata.org/wiki/"
        # iknow url
        iknow_url = "https://planthub.idiv.de/iknow/wiki/"

        wiki_entites_query_uri = "https://en.wikipedia.org/w/api.php?action=query&prop=pageprops&format=json&titles="
        label_uri = wiki_entites_query_uri + label
        label_data = requests.get(label_uri)
        label_data_response = label_data.json()
        for page in label_data_response["query"]["pages"].values():
            if ("pageprops" in page and "wikibase_item" in page["pageprops"]):
                wikibase_item = page["pageprops"]["wikibase_item"]
                url = wiki_url + wikibase_item
                return url
            else:
                return iknow_url + "C50"

    def add_class(self, g, sgpcID, uri, label=""):
        """
        e.g.
        [wiki:Q30513971] [a] [owl:Class] ;
                    [rdfs:label] ["flower_beg"] .
        """
        subject = URIRef(uri)
        g.add((subject, RDF.type, OWL.Class))
        if label != "":
            g.add((subject, RDFS.label, Literal(label)))

        g.add((subject, RDFS.seeAlso, Literal("sgpc_" + sgpcID)))

    def add_entities_string(self, g, column, mapping_column, header_class):
        """
        e.g.
        [<http://www.wikidata.org/entity/Q158008>] [instance_of] [wiki:Q7432] ;
                    [rdfs:label] ["Achillea-millefoluim"]
        """
        for i in range(len(column)):
            # e.g. [(URI of) Achillea] [is_type] [(URI of) Species]
            g.add((
                URIRef(mapping_column[i]), RDF.type, URIRef(header_class)
            ))

            # e.g. [(URI of) Achillea] [has_label] [Achillea Millefolium]
            g.add((
                URIRef(mapping_column[i]), RDFS.label, Literal(column[i])
            ))

    def add_properties(self, g, sgpcID, uri, oType, label=""):
        """
        e.g.
        [wiki:Q30513971] [a] OWL.ObjectProperty;
                    [rdfs:label] ["flower_beg"] .
        """
        subject = URIRef(uri)
        if (oType == "String"):
            g.add((subject, RDF.type, OWL.ObjectProperty))
        elif (oType == "Integer"):
            g.add((subject, RDF.type, OWL.DatatypeProperty))
        if label != "":
            g.add((subject, RDFS.label, Literal(label)))

        g.add((subject, RDFS.seeAlso, Literal("sgpc_" + sgpcID)))

    def add_row_obseration(self, g, sgpc, sgpcID, original_row, cea_row, col_types, header_labels, row_obs_properties):
        """
        e.g.
        [row-observation] [iknow:P0] [<http://www.wikidata.org/entity/Q236049>];
                    [iknow:P1] [<http://www.wikidata.org/entity/Q158008>] ;
                    [iknow:P2] ["909"] ;
                    [iknow:P3] ["2020"] ;
                    [iknow:P4] ["79"] .
        """

        global row_observation_index
        # row_obs_properties_url = f"https://planthub.idiv.de/iknow/wiki/SGPC_{sgpcID}_P"
        row_obs_properties_url = f"https://planthub.idiv.de/iknow/wiki/P{sgpcID}_R"
        for i, value in enumerate(original_row):
            print("value", i, value)
            row_obs_property_label = "has_" + header_labels[i]
            row_obs_property_url = sgpc.get_property_uri(row_obs_property_label)
            if row_obs_property_url is None:
                row_obs_property_url = get_property_url_by_label(row_obs_property_label)
                if row_obs_property_url is None:
                    row_obs_property_url = row_obs_properties_url + str(i)
            # print(col_types[i])
            g.add((
                URIRef(f"{self.IKNOW_RO}_sgpc_{sgpcID}_{row_observation_index}"),
                RDF.type,
                URIRef(f"{self.IKNOW_RO}")
            ))

            g.add((
                URIRef(f"{self.IKNOW_RO}_sgpc_{sgpcID}_{row_observation_index}"),
                RDFS.seeAlso,
                Literal("sgpc_" + sgpcID)
            ))

            if col_types[i] == "String":
                # Create new properties with label has_col_header label and assign url to them and seeAlso
                # print("Adding Cell String")
                # print(f"{value} {cea_row[i]}")
                g.add((
                    URIRef(f"{self.IKNOW_RO}_sgpc_{sgpcID}_{row_observation_index}"),
                    # URIRef(row_obs_properties_url + str(i)),
                    URIRef(row_obs_property_url),
                    URIRef(cea_row[i])
                ))
            else:
                # print("Adding Cell NON-String")
                g.add((
                    URIRef(f"{self.IKNOW_RO}_sgpc_{sgpcID}_{row_observation_index}"),
                    URIRef(row_obs_property_url),
                    Literal(value)
                ))

            # add property
            self.add_properties(g, sgpcID, row_obs_property_url, col_types[i], row_obs_property_label)

    def add_SubClass_Mappings(self, g, sgpcID, subclassMappings):
        for i, subClassMap in subclassMappings.items():
            g.add((
                URIRef(subClassMap['s']),
                RDFS.subClassOf,
                URIRef(subClassMap['o']),
            ))

            # TODO: add label and sgpc_124 to Object olabel
            g.add((
                URIRef(subClassMap['o']),
                RDFS.label,
                Literal(subClassMap['olabel']),
            ))

            g.add((
                URIRef(subClassMap['o']),
                RDFS.seeAlso,
                Literal("sgpc_" + sgpcID),
            ))

    def main(self, g, sgpc_pk, dformat, ro_startingindex=0, property_stratingIndex=10):

        # TODO:
        #   - replace row_observation_index with
        #   [ID of the SGP + '-' + local row observation index] to make it unique

        global row_observation_index
        row_observation_index = ro_startingindex

        # store header maps
        header_mapping = []
        row_obs_properties = []

        # header_map = ["https://www.wikidata.org/wiki/Q167346",
        #               "https://www.wikidata.org/wiki/Q7432",
        #               "https://planthub.idiv.de/iknow/wiki/C99",
        #               "https://www.wikidata.org/wiki/Q577",
        #               "https://www.wikidata.org/wiki/Q30513971"]

        # row_obs_properties = [
        #     "https://planthub.idiv.de/iknow/wiki/P0",
        #     "https://planthub.idiv.de/iknow/wiki/P1",
        #     "https://planthub.idiv.de/iknow/wiki/P2",
        #     "https://planthub.idiv.de/iknow/wiki/P3",
        #     "https://planthub.idiv.de/iknow/wiki/P4",
        # ]

        sgpc = sgpc_from_key(sgpc_pk)
        sgps = sgpc.associated_sgprojects.all()
        for sgp in sgps:
            generate_missing_entities(sgp, sgpc_pk)
            original_file_path = sgp_get_input_file(sgp)
            cea_file_path = sgp_get_mapping_file(sgp)
            col_types = sgp_get_col_types(sgp)

            # print("original_file_path", original_file_path)
            # print("cea_file_path", cea_file_path)
            # print("col_types", col_types)

            original_df = pd.read_csv(original_file_path.file_field.path)
            cea_df = pd.read_csv(cea_file_path.file_field.path)

            self.add_rowobservation_class(g, sgpc_pk)

            for i, mapping in sgp.provenanceRecord["0"]["selection"]["mapping"].items():
                header_mapping.append(mapping)

            header_labels = list(original_df.columns)
            for i, mapping in enumerate(header_mapping):
                # if the column type is string we define a class for that
                if col_types[i] == "String":
                    self.add_class(g, sgpc_pk, mapping, label=header_labels[i])
                else:
                    # TODO: define datatype for columns with numerical values
                    pass

            # dd properties
            for i in range(len(original_df.columns)):
                col = original_df.iloc[:, i]
                mapping_col = cea_df.iloc[:, i]

                if col_types[i] == "String":
                    self.add_entities_string(g, col, mapping_col, header_mapping[i])
                else:
                    # TODO: - implement according to RDF Structure
                    pass

            self.add_SubClass_Mappings(g, sgpc_pk, sgpc.subclassMappings)

            # add properties - user defined ones
            for mapping in sgpc.cpaMappings.values():
                print("maping", mapping)
                oIndex_orig_col = list(sgp.provenanceRecord["0"]["selection"]["child"].values()).index(mapping[5])
                # original_df.columns.tolist().index(mapping[5])
                typeof_oIndex = sgp.provenanceRecord["0"]["selection"]["type"][str(oIndex_orig_col)]
                self.add_properties(g, sgpc_pk, mapping[2], typeof_oIndex, mapping[3])

            sgp_append_downloading_step(sgp)

        for i in range(len(original_df)):
            self.add_row_obseration(g, sgpc, sgpc_pk, original_df.iloc[i], cea_df.iloc[i],
                                    col_types, header_labels, row_obs_properties)
            row_observation_index += 1

        # for i, row in enumerate(original_df.iterrows()):
        #     print(type(row))
        #     add_row_obseration(g, sgpc_pk,row, cea_df.iloc[i], col_types)

        # this is wikidata suclass URI, but we use rdfs.subclassof
        # URIRef("https://www.wikidata.org/wiki/Property:P279")

        # (in general, more specific at the bottom)
        # TODO: - for any other content or triple that needs to be in the graph
        #       - feed this information to the script, and generate triples with
        #       - g.add((s,p,o))

        # HARDCODED (these will just be read
        # from the database and become an input here)
        # g.add((
        #     URIRef("https://www.wikidata.org/wiki/Q167346"),
        #     RDFS.subClassOf,
        #     URIRef("http://www.wikidata.org/entity/Q22652")
        # ))

        # g.add((
        #     URIRef("http://www.wikidata.org/entity/Q22652"),
        #     RDFS.label,
        #     Literal("green space")
        # ))

        # g.add((
        #     URIRef("http://www.wikidata.org/entity/Q22652"),
        #     RDF.type,
        #     OWL.Class
        # ))

        # g.add((
        #     URIRef("https://www.wikidata.org/wiki/Q7432"),
        #     URIRef(f"{IKNOW}P33"),
        #     URIRef("https://www.wikidata.org/wiki/Q167346")
        # ))

        # g.add((
        #     URIRef(f"{IKNOW}P33"),
        #     RDFS.label,
        #     Literal("is_monitored_in")
        # ))

        # g.add((
        #     URIRef(f"{IKNOW}P33"),
        #     RDF.type,
        #     OWL.ObjectProperty
        # ))

        # g.add((
        #     URIRef("https://planthub.idiv.de/iknow/wiki/P0"),
        #     RDF.type,
        #     OWL.ObjectProperty
        # ))

        # g.add((
        #     URIRef("https://planthub.idiv.de/iknow/wiki/P1"),
        #     RDF.type,
        #     OWL.ObjectProperty
        # ))

        # g.add((
        #     URIRef("https://planthub.idiv.de/iknow/wiki/P2"),
        #     RDF.type,
        #     OWL.DatatypeProperty
        # ))

        # g.add((
        #     URIRef("https://planthub.idiv.de/iknow/wiki/P3"),
        #     RDF.type,
        #     OWL.DatatypeProperty
        # ))

        # g.add((
        #     URIRef("https://planthub.idiv.de/iknow/wiki/P4"),
        #     RDF.type,
        #     OWL.DatatypeProperty
        # ))

        # g.add((
        #     URIRef("https://planthub.idiv.de/iknow/wiki/P0"),
        #     RDFS.label,
        #     Literal("has_Garden")
        # ))

        # g.add((
        #     URIRef("https://planthub.idiv.de/iknow/wiki/P1"),
        #     RDFS.label,
        #     Literal("has_Species")
        # ))

        # g.add((
        #     URIRef("https://planthub.idiv.de/iknow/wiki/P2"),
        #     RDFS.label,
        #     Literal("has_AccSpeciesID")
        # ))

        # g.add((
        #     URIRef("https://planthub.idiv.de/iknow/wiki/P3"),
        #     RDFS.label,
        #     Literal("has_year")
        # ))

        # g.add((
        #     URIRef("https://planthub.idiv.de/iknow/wiki/P4"),
        #     RDFS.label,
        #     Literal("has_flower_beg")
        # ))

        # this generates rdf from the graph g in a specific format
        # g.serialize(format="ttl")

        # print(g.serialize(format="ttl"))

        # generate and write to file
        # g.serialize(destination="test_result.ttl", format="ttl")
        return HttpResponse(g.serialize(format=dformat))
        # return HttpResponse(g.serialize(format="ttl"), content_type='application/x-turtle')

    # Test run
    # TODO: - replace with actual function call from backend
    #       - load the hardcoded parts, CPA, CTA, CEA from backend
    #       - create unique entries in the database for newly created uris
    #         (this is achieved relatively easy with the django get_or_create function)
    #         https://docs.djangoproject.com/en/4.1/ref/models/querysets/#get-or-create
    #         which is already used in some places of the backend

    # https://planthub.idiv.de/iknow/wiki/ - namespace
    # https://planthub.idiv.de/iknow/wiki/C1 - classes
    # https://planthub.idiv.de/iknow/wiki/P1 - property
    # https://planthub.idiv.de/iknow/wiki/E1 - entitiy

    def get(self, request):
        """
        Generate a ttl based on sgpc key and format
        """

        # creates the graph object which holds all triples as nodes and edges
        g = Graph()

        # binding a namespace to the graph
        g.bind("wiki", self.WIKI)
        g.bind("iknow", self.IKNOW)
        g.bind("owl", OWL)

        # get parameters from request
        sgpc_pk = request.GET.get('sgpc_pk', default=None)
        dformat = request.GET.get('dformat', default='ttl')

        # response = self.main("/home/suresh/Uni_Jena/Related Documents/Codes/ttl/rdf_generation/original.csv",
        # "/home/suresh/Uni_Jena/Related Documents/Codes/ttl/rdf_generation/cea.csv",
        #                      ["String", "String", "String", "Integer", "Integer"],
        #                      header_mapping, row_obs_properties)

        response = self.main(g, sgpc_pk, dformat)

        if dformat == 'json-ld':
            dformat = 'json'

        response['Content-Disposition'] = 'attachment; filename="results.' + dformat
        return response


# Blazegraph running
# install docker from the below link
# https://www.digitalocean.com/community/tutorials/how-to-install-and-use-docker-on-ubuntu-20-04
# run command: docker run -p 9999:8080 <blazegraph_container_name>
# e.g. docker run -p 9999:8080 researchspace/blazegraph


class TTL_to_blazegraph(APIView):
    def get(self, request):
        # get parameters from request
        sgpc_pk = request.GET.get('sgpc_pk', default=None)
        sgpc = sgpc_from_key(sgpc_pk)

        if sgpc is False:
            return jr_error

        collection_name = "sgpc_" + str(sgpc.pk) + "_" + sgpc.bioprojectname
        sgpc.collectionname = collection_name
        sgpc.createdAt = date.today()
        # TODO: sgpc.createdBy = get user info from
        sgpc.save()
        collection_name_url = "https://planthub.idiv.de/iknow/" + collection_name + ".org"
        # url = "http://localhost:9999/blazegraph/namespace/kb/sparql?context-uri=" + collection_name_url
        url = settings.BLAZEGRAPH_URL + 'bigdata/sparql?context-uri=' + collection_name_url
        headers = {'Content-Type': 'application/x-turtle'}
        generateTTL = GenerateTTL()

        # creates the graph object which holds all triples as nodes and edges
        g = Graph()

        # binding a namespace to the graph
        g.bind("wiki", generateTTL.WIKI)
        g.bind("iknow", generateTTL.IKNOW)
        g.bind("owl", OWL)

        # response = self.main("/home/suresh/Uni_Jena/Related Documents/Codes/ttl/rdf_generation/original.csv",
        # "/home/suresh/Uni_Jena/Related Documents/Codes/ttl/rdf_generation/cea.csv",
        #                      ["String", "String", "String", "Integer", "Integer"],
        #                      header_mapping, row_obs_properties)

        response = generateTTL.main(g, sgpc_pk, "ttl")

        requests.post(url, data=response, headers=headers)

        # update kg metadata
        self.updateKgMeta(sgpc)

        # TODO: check uploading was successful or not
        return Response()

    def updateKgMeta(self, sgpc):
        # TODO:
        # update list of classes, properties and cpamappings
        # dont add iknow entitites

        save_cpamappings(sgpc.cpaMappings)
        for sgp in sgpc.associated_sgprojects.all():
            for (i, header) in sgp.provenanceRecord["0"]["selection"]["child"].items():
                headerUri = sgp.provenanceRecord["0"]["selection"]["mapping"][i]
                save_iknow_class(header, headerUri)

        for cpaMap in sgpc.cpaMappings.values():
            save_iknow_property(cpaMap[3], cpaMap[2])


def sparql_query2(myQueryText):
    # test = "SELECT DISTINCT * WHERE {    ?s ?p ?o .  FILTER (strstarts(str(?o),'"+ myQueryText+"'))}LIMIT 1000"
    query = "SELECT DISTINCT ?o  WHERE {   ?s rdfs:seeAlso ?o .  ?s rdfs:label '" + myQueryText + "' }"
    # TODO: correct the query
    return query


def fetch_provenance_blazegraph(myQueryText):
    url = settings.BLAZEGRAPH_URL + 'bigdata/sparql'
    print(url)

    # url = 'http://localhost:9999/blazegraph/namespace/kb/sparql'
    # print('url is:: from models.py ', url)

    headers = {
        'Accept': 'application/sparql-results+json,text/turtle'
    }
    # print('******we are prinitng content of new query')
    # print(sparql_query2(myQueryText))
    params = {'query': sparql_query2(myQueryText)}
    response = requests.get(url=url, params=params, data=None, headers=headers)
    return json.loads(response.content)


class FetchProvenance(APIView):
    def post(self, request):
        """
        Finds all sgpc's based on the queryText provided
        """
        print('***************I am in FetchProvenance')
        # get queryText
        x: dict = json.loads(request.body)["queryText"]
        json_content = fetch_provenance_blazegraph(x)
        print('------------------------json_content in Find Provenance-----------------------')
        print("json_content", json_content)

        list_of_collectionsID = []
        for binding in json_content["results"]["bindings"]:
            get_sgpcID = binding['o']["value"].split("_")[1]
            list_of_collectionsID.append(get_sgpcID)

        sgpc_collections_info = sgpc_info_by_collection_name(list_of_collectionsID)
        print("----------sgc_collections_info", sgpc_collections_info)

        response = HttpResponse({"tabledata": sgpc_collections_info})
        response['Content-Disposition'] = 'attachment; filename="results.json"'
        # print(type(json_content))
        print('+++ response before return', response)
        print('+++ json_content before return', json_content)

        return response


@api_view(['GET'])
def get_history(request):
    """
    Returns history from provance record.
    """
    # get parameters from request
    sgpc_pk = request.GET.get('sgpc_pk', default=None)
    sgpc = sgpc_from_key(sgpc_pk)

    if sgpc is False:
        return jr_error

    response_data = {}

    response_data['history'] = sgpc_history_renamed(sgpc)
    response = JsonResponse(response_data)
    return response

# Provenance retrieval pages
#   - Download workflow
#   - show time
# commit to git
# Assign a url for new properties
# Assign a url and seeAlso for new class on schemarefinement
# show subclass labels


# Row observation and attach all columns to it
# Add iknow property check in add_row_observation
# download different version of ttl -- Pending
# add goto on query building and download


# Query building page: Call eriks function
# Add query meta data to work
#   - Column name:: {"0": "Species", "1": "Garden"}
#   - Column type:: {"0": "String", "1": "Integer"}
# csv with , and ; or tell the separate -- pending
# User login
# delete duplicate on schemarefinement
