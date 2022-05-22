# flake8: noqa
from django.shortcuts import render
from .read_data import get_active_dataset
from django.http import JsonResponse

from . import (
    bar,
    histogram,
    pie,
    scatter_3D_cat,
    scatter_cat,
    scatter_cont,
    scatter_matrix_cat,
    violin,
)  # this import is needed, so keep it!


def get_datasets(request):
    return JsonResponse(get_active_dataset(), safe=False)


# Create your views here.


def get_context(request):
    print(request.GET.get("default_ds"))

    dataframe_value = "TRY"  # Todo retrieve from DB
    if request.GET.get("default_ds"):
        dataframe_value = request.GET.get("default_ds")
    if request.GET.get("default_ds_id"):
        dataframe_value_id = request.GET.get("default_ds_id")
        # Todo  get name from dataset

    context = {
        'args': {
            'dataframe': {
                'value': dataframe_value
            }
        }
    }
    return context


def pie(request):
    context = get_context(request)
    return render(request, 'viz/pie.html', context=context)


def bar(request):
    context = get_context(request)
    return render(request, 'viz/bar.html', context=context)


def violin_view(request):
    context = get_context(request)
    return render(request, 'viz/violin.html', context=context)


def scatter_cat(request):
    context = get_context(request)
    return render(request, 'viz/scatter_cat.html', context=context)


def scatter_cont(request):
    context = get_context(request)
    return render(request, 'viz/scatter_cont.html', context=context)


def scatter_3D_cat(request):
    context = get_context(request)
    return render(request, 'viz/scatter_3D_cat.html', context=context)


def scatter_matrix_cat(request):
    context = get_context(request)
    return render(request, 'viz/scatter_matrix_cat.html', context=context)


def histogram(request):
    context = get_context(request)
    return render(request, 'viz/histogram.html', context=context)


def choose_plot(request):
    context = get_context(request)
    return render(request, 'viz/choose_plot.html', context=context)
