from django.shortcuts import render
from . import pie, bar, violin, scatter_cat, scatter_cont, scatter_3D_cat, histogram, scatter_matrix_cat


# Create your views here.


def pie(request):
    return render(request, 'viz/pie.html')


def bar(request):
    return render(request, 'viz/bar.html')


def violin_view(request):
    return render(request, 'viz/violin.html')


def scatter_cat(request):
    return render(request, 'viz/scatter_cat.html')


def scatter_cont(request):
    return render(request, 'viz/scatter_cont.html')


def scatter_3D_cat(request):
    return render(request, 'viz/scatter_3D_cat.html')

def scatter_matrix_cat(request):
    return render(request, 'viz/scatter_matrix_cat.html')

def histogram(request):
    return render(request, 'viz/histogram.html')


def choose_plot(request):
    return render(request, 'viz/choose_plot.html')
