from django.urls import path
from . import views

app_name = 'silenus'

urlpatterns = [
    path(r'checkForWork/', views.checkForWork),
]


# urlpatterns = [
#     path(r'csv/', views.processcsv),
#     path(r'createdata/', views.createData),
# ]

# solvepatterns = []
# for u in urlpatterns:
#     pattern = eval(u.pattern.describe())
#     solvepatterns.append(path(pattern+r"solve", u.callback))
#     solvepatterns.append(path(pattern+r"solve/", u.callback))

# urlpatterns = urlpatterns+solvepatterns