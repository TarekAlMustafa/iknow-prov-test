from django.urls import path

from .views import (
    ChangeDatasetAndRerunView,
    CleaningView,
    CopyCollectionView,
    CreateCollectionView,
    DatasetInit,
    DeleteDBView,
    EditCpaView,
    EditMappingsView,
    EditSchemaView,
    FetchBioprojectNamesView,
    FetchCollectionProvenance,
    FetchCpaView,
    FetchDataView,
    FetchSubclassesView,
    LinkingView,
    RerunCollectionView,
    ResetCollectionView,
    SGPCInfoView,
    UploadToCollectionView,
)

urlpatterns = [
    # parameterized ... has urlparams
    # unique ... fetched by only one svelte page
    # multiple ... fetched by multiple svelte-pages (branches accordingly)

    # create new sgproject, [unique]
    # path('create-sgproject', CreateProjectView.as_view()),
    # path('create-sgproject', ProjectView.as_view()),

    path('create-collection', CreateCollectionView.as_view()),

    path('upload-datasets-to-collection', UploadToCollectionView.as_view()),

    path('fetch-datasets-from-collection', FetchDataView.as_view()),

    # path('tools-workflow-info', ToolView.as_view()),

    # saves datasets, - datasetentries and attaches them to specific sgproject
    # at the moment [unique, parameterized]
    # path('datasetupload', DataUploadView.as_view()),

    # on post: creates init step in sgproject and saves actions
    # [unique, parameterized]
    path('datasets_init', DatasetInit.as_view()),

    # on get: not implemented yet (might be merged later)
    # on post: initiates cleaning on datasets, creates new dataset-versions
    # at the moment [unique, parameterized]
    path('apply_cleaning', CleaningView.as_view()),

    # on get: not implemented yet (might be merged later)
    # on post: initiates linking on datasets, creates new dataset-versions
    # at the moment [unique, parameterized]
    path('apply_linking', LinkingView.as_view()),

    path('fetch-bioproject-names', FetchBioprojectNamesView.as_view()),

    path('all-sgpc-info', SGPCInfoView.as_view()),


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

    path('fetch-collection-provenance', FetchCollectionProvenance.as_view()),

    path('resetcollectionto', ResetCollectionView.as_view()),

    path('copy-collection', CopyCollectionView.as_view()),

    path('rerun-collection', RerunCollectionView.as_view()),

    path('change-datasets-and-rerun', ChangeDatasetAndRerunView.as_view()),

    path('delete-database', DeleteDBView.as_view()),
]
