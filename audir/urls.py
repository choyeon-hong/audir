from django.urls import path
from . import views

app_name = 'audir'

urlpatterns = [
    path('', views.index, name='index'),
    path('projects/', views.project_list, name='project_list'),
    path('projects/create/', views.create_project, name='create_project'),
    path('projects/<int:project_id>/', views.project_detail, name='project_detail'),
    path('projects/delete-selected-proj/', views.delete_selected_projects, name='delete_selected_projects'),
    path('projects/delete-selected-img/', views.delete_selected_images, name='delete_selected_images'),
    path('generate-csv/', views.generate_csv, name='generate_csv'),
    path('result-detail/<int:result_id>/', views.result_detail, name='result_detail'),
    path('about/', views.about, name='about'),
    path('how-it-works/', views.how_it_works, name='how_it_works'),
]
