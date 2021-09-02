from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from planthub.datasets.models import Dataset, File, Datastructure, DatastructureInline
#from suit.admin import SortableListForm


class DatastructureInline(admin.TabularInline):
    model = DatastructureInline
    #fields = ('order','viz', 'download')
    extra = 0
    #verbose_name_plural = ''
    #sortable = 'order'

@admin.register(Dataset)
class DatasetsAdmin(admin.ModelAdmin):
    list_display = ('title', 'description')

@admin.register(File)
class FilesAdmin(admin.ModelAdmin):
    list_display = ('dataset', 'file_name', 'version', 'file_size')

@admin.register(Datastructure)
class DatastructuresAdmin(admin.ModelAdmin):
    list_display = ('name',)
    inlines = (DatastructureInline,)
