from django.contrib import admin

from .models import CPAmapping, IKNOWclass, IKNOWproperty, QueryMetaData

admin.site.register(CPAmapping)
admin.site.register(IKNOWclass)
admin.site.register(IKNOWproperty)
admin.site.register(QueryMetaData)
