from django.urls import path

from .views import (
    ChangeFileAndRerunView,
    CleaningView,
    ColumntypesView,
    CopySgpcView,
    CreateSgpcView,
    DeleteDBView,
    EditCpaView,
    EditMappingsView,
    EditSchemaView,
    FetchCpaView,
    FetchDataView,
    FetchSubclassesView,
    LinkingView,
    RerunView,
    UndoSgpcView,
    UploadToSgpcView,
    get_bioproject_names,
    get_sgpc_info,
    get_sgpc_provenance,
    GenerateTTL,
    TTL_to_blazegraph
)

urlpatterns = [
    # parameterized ... has urlparams
    # unique ... fetched by only one svelte page
    # multiple ... fetched by multiple svelte-pages (branches accordingly)

    # create new sgproject, [unique]
    # path('create-sgproject', CreateProjectView.as_view()),
    # path('create-sgproject', ProjectView.as_view()),

    path('create-collection', CreateSgpcView.as_view()),

    path('upload-datasets-to-collection', UploadToSgpcView.as_view()),

    path('fetch-datasets-from-collection', FetchDataView.as_view()),

    # path('tools-workflow-info', ToolView.as_view()),

    # saves datasets, - datasetentries and attaches them to specific sgproject
    # at the moment [unique, parameterized]
    # path('datasetupload', DataUploadView.as_view()),

    # on post: creates init step in sgproject and saves actions
    # [unique, parameterized]
    path('datasets_init', ColumntypesView.as_view()),

    # on get: not implemented yet (might be merged later)
    # on post: initiates cleaning on datasets, creates new dataset-versions
    # at the moment [unique, parameterized]
    path('apply_cleaning', CleaningView.as_view()),

    # on get: not implemented yet (might be merged later)
    # on post: initiates linking on datasets, creates new dataset-versions
    # at the moment [unique, parameterized]
    path('apply_linking', LinkingView.as_view()),

    path('fetch-bioproject-names', get_bioproject_names, name="get_bioproject_names"),

    path('all-sgpc-info', get_sgpc_info, name="get_sgpc_info"),


    # returns dataset data etc. for specific sgproject
    # this might be a good one to merge into
    # [multiple, parameterized]
    # path('datasets_data', DatasetDataView.as_view()),



    # -------------------------------------------------#

    path('fetch-cpa', FetchCpaView.as_view()),

    path('fetchSubclasses', FetchSubclassesView.as_view()),

    path('editMappings', EditMappingsView.as_view()),

    path('editcpa', EditCpaView.as_view()),

    path('editschema', EditSchemaView.as_view()),

    path('fetch-collection-provenance', get_sgpc_provenance, name="get_sgpc_provenance"),

    path('resetcollectionto', UndoSgpcView.as_view()),

    path('copy-collection', CopySgpcView.as_view()),

    path('rerun-collection', RerunView.as_view()),

    path('change-datasets-and-rerun', ChangeFileAndRerunView.as_view()),

    path('delete-database', DeleteDBView.as_view()),

    path('generate-ttl', GenerateTTL.as_view()),

    path('ttl-to-blazegraph', TTL_to_blazegraph.as_view()),


]
