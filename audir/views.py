from django.shortcuts import render, redirect
from django.urls import reverse
from .models import Image, Project, Result
import cv2
import numpy as np
import mediapipe as mp
from django.shortcuts import get_object_or_404
from django.core.paginator import Paginator

import csv
from django.http import HttpResponse

from allauth.account.views import PasswordChangeView
import os
from django.conf import settings
from mediapipe.python.solutions.drawing_utils import draw_landmarks
from mediapipe.python.solutions.hands import HAND_CONNECTIONS
from mediapipe.python.solutions.drawing_styles import get_default_hand_landmarks_style
from mediapipe.python.solutions.drawing_styles import get_default_hand_connections_style


#main page
def index(request) :
    context = {}
    return render(request, 'audir/index.html', {'context': context})

def calculate_distance(p1, p2):
    #Euclidean distance
    #the data type of input are tuples -> np.array(p1)
    return np.sqrt(np.sum((np.array(p1)-np.array(p2))**2))

def process_image(image_path, result_filename):

    #read the image from the path
    image = cv2.imread(image_path)
    #convert BGR into RGB for MediaPipe
    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

    #choose the mode and limit the max num of hands to detect
    with mp.solutions.hands.Hands(static_image_mode=True, max_num_hands=1) as hands:

        #process() info from https://github.com/google-ai-edge/mediapipe/blob/master/mediapipe/python/solutions/hands.py
        #process() method returns NamedTuple
        results = hands.process(image_rgb)

        #if nothing is detected -> returns nones to avoid errors
        if not results.multi_hand_landmarks or not results.multi_handedness:
            return None, None, None, None, None
        
        landmarks = results.multi_hand_landmarks[0] # 1st detected hand : max_num_hands=1 -> only one hand is detected
        world_landmarks = results.multi_hand_world_landmarks[0]
        #https://mediapipe.readthedocs.io/en/latest/solutions/hands.html
        #handedness assumes the input image is mirrored -> swap the label
        handedness = results.multi_handedness[0].classification[0].label
        mirrored_handedness = {"Left": "Right", "Right": "Left"}.get(handedness, "N/A")

        #image.shape = (row, col, channel)
        #col : x coordinate, row : y coordinate
        #convert the landmarks into coordinates by using the image sizes
        lm = [(lm.x * image.shape[1], lm.y * image.shape[0]) for lm in landmarks.landmark]
        #measure the length of the finger-> lm[5]: MCP of index finger, lm[8] tip of index finger
        A = calculate_distance(lm[5], lm[8])
        #lm[13]: MCP of ring finger, lm[16] tip of ring finger
        B = calculate_distance(lm[13], lm[16])
        #avoid ZeroDivisionError
        ratio = A / B if B != 0 else None
        
        #print detected coordinates and handedness for debugging
        # print("5:", lm[5], "8:", lm[8], "13:", lm[13], "16:", lm[16], "left or right: ", mirrored_handedness)

        #copy the image annotate the landmarks
        annotated_image = image.copy()

        #draw_landmarks info from https://github.com/google-ai-edge/mediapipe/blob/master/mediapipe/python/solutions/drawing_utils.py
        draw_landmarks(
            annotated_image,
            landmarks,
            HAND_CONNECTIONS,
            get_default_hand_landmarks_style(),
            get_default_hand_connections_style())

        # write the image with landmarks
        result_path = os.path.join(settings.MEDIA_ROOT, 'result', result_filename)
        cv2.imwrite(result_path, annotated_image)
        #return rounded values and result path
        return round(A, 4), round(B, 4), round(ratio, 4), 'result/' + result_filename, mirrored_handedness

#create project objs and redirect to the list
def create_project(request):
    if request.method == 'POST':
        name = request.POST.get('project')
        if name:
            Project.objects.create(project=name, user=request.user)
        return redirect('audir:project_list')
    return render(request, 'audir/project_create.html')

#display the current user's projects only
def project_list(request):
    user = request.user
    projects = Project.objects.filter(user=user)

    return render(request, 'audir/project_list.html', {'projects': projects})


#previous code that is valid for a single file
# def project_detail(request, project_id):
#     #get project object or 404 error instead of try-except clause
#     project = get_object_or_404(Project, pk=project_id)
#     #image file form
#     form = HandImageForm()

#     if request.method == 'POST':
#         form = HandImageForm(request.POST, request.FILES)
#         if form.is_valid():
#             user = request.user
#             file = Image.file
#             hand_image = form.save(commit=False)
#             #project in which the image is included
#             hand_image.project = project
#             #save the image file
#             hand_image.save()
#             #extract the original filename
#             original_filename = hand_image.file.name.split('/')[-1]
#             # process_image() returns 4 args and save them in DB
#             A, B, ratio, result_rel_path = process_image(hand_image.file.path, f"result_{hand_image.id}_{user.username}_{original_filename}")
#             # create Result objects to save the detected result 
#             Result.objects.create(
#                 image=hand_image,
#                 length_index=A,
#                 length_ring=B,
#                 ratio=ratio,
#                 result_image=result_rel_path
#             )
#             #redirect to the project by using project id
#             return redirect('audir:project_detail', project_id=project.id)
#     #Display the images which are included in the project
#     images = Result.objects.filter(image__project=project)
#     return render(request, 'audir/project_detail.html', {
#         'project': project,
#         'form': form,
#         'images': images,
#     })


#upload multiple image files
def project_detail(request, project_id):
    #get project object or 404 error instead of try-except clause
    project = get_object_or_404(Project, pk=project_id)

    if request.method == 'POST':
        files = request.FILES.getlist('file')
        if files:
            #loop for multiple image files
            for uploaded_file in files:
                #includes project info to figure out each project
                hand_image = Image(project=project, file=uploaded_file)
                hand_image.save()

                #save the original filename
                original_filename = uploaded_file.name
                #define the result filename
                result_filename = f"result_{hand_image.id}_{request.user.username}_{original_filename}"
                #default progression status is 'uploaded'
                result = Result.objects.create(
                    image=hand_image,
                    progression="uploaded"
                )

                #process the image
                A, B, ratio, result_rel_path, handedness = process_image(
                    hand_image.file.path, result_filename
                )

                #save the results from process_image()
                result.length_index = A
                result.length_ring = B
                result.ratio = ratio
                result.result_image = result_rel_path
                #if the image is successfully processed, the progression will be 'done'
                result.progression = "done"
                result.handedness = handedness
                result.save()

            #redirect to the project by using project.id
            return redirect('audir:project_detail', project_id=project.id)
        
    #https://docs.djangoproject.com/en/5.2/topics/db/queries/
    #images only in the selected project are displayed and ordered by the date descending
    all_images = Result.objects.filter(image__project=project).order_by('-image__uploaded_at')
    #pagination
    page_number = request.GET.get('page')
    paginator = Paginator(all_images, 10)  #10 rows per page
    page_obj = paginator.get_page(page_number)

    return render(request, 'audir/project_detail.html', {
        'project': project,
        'images': page_obj,
        'page_obj': page_obj,
    })


#customised view : redirect to index page if pw is changed successfully
class CustomPasswordChangeView(PasswordChangeView):
    def get_success_url(self):
        return reverse('audir:index')


def delete_selected_projects(request): 
    selected_ids = request.POST.getlist('selected_projects')
    if selected_ids:
        #filter the selected projs and delete
        Project.objects.filter(id__in=selected_ids).delete()
    return redirect('audir:project_list')


def delete_selected_images(request): 
    selected_images = request.POST.getlist('selected_images')
    if selected_images:
        #filter the project owned by the current user and delete only selected images
        Image.objects.filter(id__in=selected_images,project__user=request.user).delete()
    project_id = request.POST.get('project_id')
    return redirect('audir:project_detail', project_id = project_id)


#https://www.geeksforgeeks.org/python/djnago-csv-output/
def generate_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="output.csv"'

    writer = csv.writer(response)
    #the names of cols
    writer.writerow(['Filename', 'Index Finger(A)', 'Ring Finger(B)', 'Digit ratio(A/B)'])

    selected_images = request.POST.getlist('selected_images')
    if selected_images :
        #https://docs.djangoproject.com/en/5.2/ref/models/querysets/
        #select_related : select additional related-object data when it executes its query. prepopulated -> better performance.
        images = Image.objects.filter(id__in=selected_images).select_related('result') 
        for img in images:
            result = img.result
            #remove the path and save the filename only
            filenm = (img.file.name).split('/')[-1]
            writer.writerow([filenm, result.length_index, result.length_ring, result.ratio])
    return response


def result_detail(request, result_id):
    result = get_object_or_404(Result, pk=result_id)
    return render(request, 'audir/result_detail.html', {'result': result})

def about(request):
    return render(request, 'audir/about.html')

def how_it_works(request):
    return render(request, 'audir/how_it_works.html')