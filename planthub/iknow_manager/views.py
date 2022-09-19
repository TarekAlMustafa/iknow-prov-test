import json

import pandas as pd
from django.http import HttpResponse, JsonResponse
# from iknow_tools.views import get_all_tools_workflow_info
from rest_framework.response import Response
# from distutils.log import error
# from django.db import models
# from django.shortcuts import render
from rest_framework.views import APIView

from planthub.iknow_datasets.models import Dataset
from planthub.iknow_datasets.views import create_filefield, handle_uploaded_file
from planthub.iknow_manager.models import CPAmapping, safe_querymetadata
from planthub.iknow_sgp.models import SGP
from planthub.iknow_sgp.views import (
    append_editCpa_step,
    append_editMapping_step,
    append_linking_step,
    append_schemaRefine_step,
    apply_mapping_edits_to_sgp,
    create_sgp,
    get_column_types,
    get_latest_input_dataset,
    get_latest_output_dataset,
    get_mapping_dataset,
    get_provrec,
    replace_mapping_file_with_copy,
    replace_source_dataset,
    reset_sgp_until_linking,
    set_phase_state,
    sgp_from_key,
)
from planthub.iknow_sgpc.models import SGPC
from planthub.iknow_sgpc.views import (  # get_all_header_mappings,; get_history_sgpc,
    copy_collection,
    createCollection,
    edit_cpa_mappings,
    edit_schema,
    get_all_projects_name,
    get_all_sgp_info,
    get_all_sgpc_info,
    get_history_sgpc_renamed,
    get_single_sgpc_info,
    is_in_progress_sgpc,
    sgpc_from_key,
    undo_collection_till_phase,
)

from .cleaning_scripts import findsubclasses, wikitesttool
# from .pdutil.pdconverter import append_boolean_list
from .pdutil.pdreader import (  # get_json_from_csv,; get_list_from_csv,
    get_list_from_csv_first10rows,
)

# import time

# from copyreg import constructor

jr_error = JsonResponse({"msg": "error"})
jr_error_message = {"msg": "error"}

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

        id_counter = 0

        # iterate over the files in the request
        for key, file in request.FILES.items():
            filename = request.FILES[key].name

            # create sgp and handle file
            new_dataset = handle_uploaded_file(request.FILES[key], filename)
            new_sgp = create_sgp(sgpc.bioprojectname)
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
        """
        # get parameters from request
        sgpc_pk = request.GET.get('sgpc_pk', default=None)
        sgpc = sgpc_from_key(sgpc_pk)

        if sgpc is False:
            return jr_error

        if is_in_progress_sgpc(sgpc):
            print("Error in FetchDataView: sgpc ", sgpc.pk, " is still running.")
            return jr_error

        # requires filenames, requires dataset content
        req_names = (request.GET.get('names', '') != '')
        req_datasets = (request.GET.get('datasets', '') != '')
        req_history = (request.GET.get('history', '') != '')
        req_type = request.GET.get('type', '')

        if req_type == "cleaning":
            data = self.prepare_datasets(sgpc, req_names, req_datasets, req_history)
        if req_type == "linking":
            print("preparing linking result")
            data = self.prepare_linking_result(sgpc, req_names, req_datasets, req_history)
        else:
            data = self.prepare_datasets(sgpc, req_names, req_datasets, req_history)

        # print("returning prepared datasets: ", data)
        # print(type(data))

        response = JsonResponse(data, safe=False)
        # for key in data:
        #     print(f"Key: {key} value: {data[key]}")

        # return Response()
        return response

    def prepare_linking_result(self, sgpc: SGPC, req_names: bool, req_datasets: bool, req_history: bool):
        """
        Load and return content and required information on all
        datasets in a sgpc.
        """
        prepared_datasets = {}

        for i, sgp in enumerate(sgpc.associated_sgprojects.all()):
            # print("sgp.id: ", sgp.id, " sgp.bioprojectname: ", sgp.bioprojectname)
            helper = {}
            helper["sgp_pk"] = sgp.pk

            if req_names:
                helper["filename"] = sgp.original_filename

            helper["dataset"] = self.load_unique_mappings(sgp)

            if req_history and i == 0:
                helper["history"] = get_history_sgpc_renamed(sgpc)

            prepared_datasets[i] = helper

        return prepared_datasets

    def load_unique_mappings(self, sgp):
        input_dataset = get_latest_input_dataset(sgp)
        mapping_dataset = get_mapping_dataset(sgp)

        if input_dataset is False or mapping_dataset is False:
            return jr_error_message

        input_df = pd.read_csv(input_dataset.file_field.path)
        mapping_dataset = pd.read_csv(mapping_dataset.file_field.path)

        col_types = get_column_types(sgp, binary=True)

        all_mappings = {}

        for i, col_name in enumerate(input_df):
            if col_types[i]:
                col_mappings = self.load_unique_col_mappings(input_df[col_name], mapping_dataset[col_name], col_name)
                all_mappings[str(i)] = col_mappings

        return all_mappings

    def load_unique_col_mappings(self, col, result_col, col_name):
        already_seen = []
        mappings = [[col_name, f"{col_name} links"]]

        for i, cell_value in enumerate(col):
            if cell_value not in already_seen:
                already_seen.append(cell_value)
                mappings.append([cell_value, str(result_col[i])])

        return mappings

    def prepare_datasets(self, sgpc: SGPC, req_names: bool, req_datasets: bool, req_history: bool):
        """
        Load and return content and required information on all
        datasets in a sgpc.
        """
        prepared_datasets = {}

        for i, sgp in enumerate(sgpc.associated_sgprojects.all()):
            # print("sgp.id: ", sgp.id, " sgp.bioprojectname: ", sgp.bioprojectname)
            dataset = get_latest_output_dataset(sgp)
            helper = {}
            helper["sgp_pk"] = sgp.pk

            if req_names:
                helper["filename"] = sgp.original_filename
            if req_datasets:
                helper["dataset"] = get_list_from_csv_first10rows(dataset.file_field.path)
            if req_history and i == 0:
                helper["history"] = get_history_sgpc_renamed(sgpc)

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
        sgp: SGP
        for sgp in sgpc.associated_sgprojects.all():
            for key in data["tabledata"].keys():
                if data["tabledata"][key]["sgp_pk"] == sgp.pk:
                    if len(sgp.provenanceRecord) == 0:
                        self.safe_init_step(sgp, data["tabledata"][key])
                        safe_querymetadata(data["tabledata"][key]["selection"],
                                           sgp.original_table_header, sgp.bioprojectname)
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
                input_file_path = job[1].file_field.path
                output_path = job[2].file_field.path
                method = job[3]

                # starting routine for a tool (like wikitesttool)
                # TODO:
                #   - own function, cased on method
                print(f"Running Job with method: {method} for file: {input_file_path}.")
                col_types = get_column_types(job[0])

                # RUNS QUERY ONLY FOR String-type columns!!!
                wikitesttool.main(
                    INPUT_FILE=input_file_path,
                    OUTPUT_FILE=output_path,
                    COL_TYPES=col_types)

                set_phase_state(job[0], "done")


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
        latest_dataset: Dataset = get_latest_output_dataset(sgp)
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
        all_subclasses['history'] = get_history_sgpc_renamed(sgpc)

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

        for sgp_number in data['edits']:
            sgp = sgp_from_key(sgp_number)
            if sgp is False:
                return jr_error

            apply_mapping_edits_to_sgp(sgp, data['edits'][sgp_number])
            append_editMapping_step(sgp, data['edits'])

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

        edit_cpa_mappings(sgpc, data)
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

        edit_schema(sgpc, data)

        return Response()


class ResetCollectionView(APIView):
    def post(self, request):
        data = json.loads(request.body)["data"]
        step = int(data['step'])
        sgpc_pk = data['sgpc_pk']
        sgpc = sgpc_from_key(sgpc_pk)

        if sgpc is False:
            return jr_error
        print("RESETVIEW, Step: ", step, " on sgpc: ", sgpc_pk)

        clear_schema = False
        clear_cpa = False

        for sgp in sgpc.associated_sgprojects.all():
            prov_rec = sgp.provenanceRecord
            for i in range(len(sgp.provenanceRecord)-1, step-1, -1):
                cur_type = prov_rec[str(i)]['type']
                # print("i: ", i, " ", prov_rec[str(i)]['type'])
                if cur_type == "linking":
                    del prov_rec[str(i)]
                    # TODO: Clear datasets
                elif cur_type == "cleaning":
                    del prov_rec[str(i)]
                elif cur_type == "editcpa":
                    clear_cpa = True
                    del prov_rec[str(i)]
                elif cur_type == "editmapping":
                    del prov_rec[str(i)]
                elif cur_type == "schemarefine":
                    clear_schema = True
                    del prov_rec[str(i)]
                elif cur_type == "init":
                    del prov_rec[str(i)]

            sgp.save()

        if clear_cpa:
            self.clear_cpamappings(sgpc)

        if clear_schema:
            self.clear_schema(sgpc)

        return JsonResponse({"phase": "linking"})

    def clear_schema(self, sgpc: SGPC):
        sgpc.subclassMappings = {}
        sgpc.save()

    def clear_cpamappings(self, sgpc: SGPC):
        sgpc.cpaMappings = {}
        sgpc.save()


# this view is unnecessary for now
class SGPInfoView(APIView):
    def get(self, request):
        # tic = time.perf_counter()
        response = JsonResponse({"tabledata": get_all_sgp_info()})

        # toc = time.perf_counter()
        # print(f"get_all_sgp_info() took {toc - tic:0.4f} seconds")
        return response


class SGPCInfoView(APIView):
    def get(self, request):
        # tic = time.perf_counter()

        response = JsonResponse({"tabledata": get_all_sgpc_info()})

        # toc = time.perf_counter()
        # print(f"get_all_sgpc_info() took {toc - tic:0.4f} seconds")
        return response


class SingleSGPCInfoView(APIView):
    def get(self, request):
        sgpc_pk = request.GET.get('sgpc_pk', default=None)
        response_content = {"tabledata": get_single_sgpc_info(sgpc_pk)}

        response = JsonResponse(response_content)

        return response


class FetchProvrecView(APIView):
    def get(self, request):
        sgp_pk = request.GET.get('sgp_pk', default=None)

        response_content = {"provrec": get_provrec(sgp_pk)}

        response = JsonResponse(response_content)

        return response


class FetchCollectionProvenance(APIView):
    def get(self, request):
        sgpc_pk = request.GET.get('sgpc_pk', default=None)
        sgpc = sgpc_from_key(sgpc_pk)

        if sgpc is False:
            return jr_error

        response_content = {"tabledata": {}, "sgpc_pk": sgpc_pk}

        sgp: SGP
        for i, sgp in enumerate(sgpc.associated_sgprojects.all()):
            response_content["tabledata"][i] = {}
            response_content["tabledata"][i]["provdata"] = get_provrec(sgp.pk)
            response_content["tabledata"][i]["sgp_pk"] = sgp.pk
            response_content["tabledata"][i]["filename"] = sgp.original_filename

        response = JsonResponse(response_content)

        return response


class FetchBioprojectNamesView(APIView):
    def get(self, request):
        response = JsonResponse({"projectNames": get_all_projects_name()})
        return response


class CopyCollectionView(APIView):
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

        sgpc_copy = copy_collection(sgpc)

        if reset_to_phase is not None:
            undo_collection_till_phase(sgpc_copy, int(reset_to_phase))

        return Response()


class RerunCollectionView(APIView):
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

        sgpc_copy = copy_collection(sgpc)

        # undo collection up until init
        undo_collection_till_phase(sgpc_copy, 1)

        self.rerun_sgp(sgp_data, sgpc_copy)

        self.rerun_sgpc(sgpc_copy, old_sgpc_provrec, rerun_subclasses, rerun_cpa)

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
                    latest_dataset: Dataset = get_latest_output_dataset(new_sgp)
                    print("LATEST_DATASET: ", latest_dataset)
                    output_file = create_filefield(
                        self.suffix_filename_with_sgp(new_sgp, "output.csv"))

                    print("OUTPUT_FILE: ", output_file)
                    append_linking_step(new_sgp, -1, latest_dataset.pk, output_file.pk)
                    self.run_linking_tool(new_sgp, latest_dataset, output_file)

                elif phase['type'] == 'editmapping':
                    if "edits" in phase:
                        apply_mapping_edits_to_sgp(new_sgp, phase['edits'])
                        append_editMapping_step(new_sgp, phase['edits'])
                    else:
                        append_editMapping_step(new_sgp, {})
                elif phase['type'] == 'editcpa':
                    append_editCpa_step(new_sgp)
                elif phase['type'] == 'schemarefine':
                    append_schemaRefine_step(new_sgp)

    def rerun_sgpc(self, sgpc: SGPC, old_sgpc_provrec: dict, rerun_subclasses, rerun_cpa):
        if rerun_subclasses:
            # TODO: - DRY, move everything after method call into method find_subclasses
            find_subclasses(sgpc)

        if rerun_cpa:
            find_mappings(sgpc)

        for key, phase in old_sgpc_provrec.items():
            if phase['type'] == 'editcpa':
                if "edits" in phase:
                    edit_cpa_mappings(sgpc, phase['edits'])
                else:
                    edit_cpa_mappings(sgpc, {'deleted': {}, 'added': {}})
            elif phase['type'] == 'schemarefine':
                if "edits" in phase:
                    edit_schema(sgpc, phase['edits'])
                else:
                    edit_schema(sgpc, {'deleted': {}, 'added': {}})

    def run_linking_tool(self, sgp, latest_dataset, output_file):
        # assign necessary information
        input_file_path = latest_dataset.file_field.path
        output_path = output_file.file_field.path
        # method = job[3]

        # starting routine for a tool (like wikitesttool)
        # TODO:
        #   - own function, cased on method
        # print(f"Running Job with method: {method} for file: {input_file_path}.")
        col_types = get_column_types(sgp)

        # RUNS QUERY ONLY FOR String-type columns!!!
        wikitesttool.main(
            INPUT_FILE=input_file_path,
            OUTPUT_FILE=output_path,
            COL_TYPES=col_types)

        set_phase_state(sgp, "done")

    def suffix_filename_with_sgp(self, sgp, filename: str):
        """
        Creates a unique filename based on sgp key and length
        of the provenance record. [Change this later!]
        """
        return f"{sgp.pk}_{len(sgp.provenanceRecord)}_{filename}"


class ChangeDatasetAndRerunView(APIView):
    def post(self, request):
        sgpc_pk = request.GET.get('sgpc_pk', default=None)
        sgpc = sgpc_from_key(sgpc_pk)

        if sgpc is False:
            return jr_error

        new_sgpc = copy_collection(sgpc)
        undo_collection_till_phase(new_sgpc, 1)

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
                            replace_source_dataset(new_sgp, new_dataset)

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
                replace_mapping_file_with_copy(new_sgp)
                reset_sgp_until_linking(new_sgp)
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
                    latest_dataset: Dataset = get_latest_output_dataset(new_sgp)
                    output_file = create_filefield(
                        self.suffix_filename_with_sgp(new_sgp, "output.csv"))
                    append_linking_step(new_sgp, -1, latest_dataset.pk, output_file.pk)
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
        col_types = get_column_types(sgp)

        # RUNS QUERY ONLY FOR String-type columns!!!
        wikitesttool.main(
            INPUT_FILE=input_file_path,
            OUTPUT_FILE=output_path,
            COL_TYPES=col_types)

        set_phase_state(sgp, "done")

    def suffix_filename_with_sgp(self, sgp, filename: str):
        """
        Creates a unique filename based on sgp key and length
        of the provenance record. [Change this later!]
        """
        return f"{sgp.pk}_{len(sgp.provenanceRecord)}_{filename}"


class DeleteDBView(APIView):
    def post(self, request):
        for d in Dataset.objects.all():
            if d.pk > 647:
                d.delete()

        for sgp in SGP.objects.all():
            if sgp.pk > 507:
                sgp.delete()

        for sgpc in SGPC.objects.all():
            print(sgpc.pk)
            if sgpc.pk > 308:
                sgpc.delete()

        return Response()


def find_subclasses(sgpc: SGPC):
    """
    Generates subclass-mappings based on data in the collection and
    fetched results from the wikidata endpoint.
    """
    headers = []
    for sgp in sgpc.associated_sgprojects.all():
        for entry in sgp.provenanceRecord['0']['selection']['mapping'].values():
            headers.append(entry)
    result = findsubclasses.main(headers, "")

    counter = 0
    subclasses_to_save = {}
    for s in result:
        for parent in result[s]['parentclasses']:
            helper = {'s': result[s]['label'], 'o': parent}
            subclasses_to_save[str(counter)] = helper
            counter += 1

    sgpc.subclassMappings = subclasses_to_save
    sgpc.save()


def find_mappings(sgpc: SGPC):
    """
    Generates cpa-mappings based on data in the collection and
    the manually inserted CPAmapping database entries.
    """
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


def get_next_unused_key(somedic: dict):
    for i in range(10000):
        if str(i) in somedic:
            i += 1
        else:
            return str(i)

    return False
