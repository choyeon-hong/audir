from django.test import TestCase
from django.urls import reverse
from audir.models import User, Project, Image, Result

from django.contrib.auth import get_user_model 
from django.urls import reverse
import os
from django.test import TestCase, Client, override_settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.conf import settings

import csv
import io

User = get_user_model()

class Tests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password')
        self.project = Project.objects.create(user=self.user, project='Test Project')
        self.client = Client()
        self.client.force_login(self.user)

    def test_user_is_created(self):
        user_exists = User.objects.filter(username='testuser').exists()
        print("====user===",User.objects.all())
        self.assertTrue(user_exists)

    def test_login(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse('audir:project_list'))
        self.assertEqual(response.status_code, 200)

    def test_create_project(self):
        response = self.client.post(reverse('audir:create_project'), {'project': 'Testing'}, follow=True)
        self.assertEqual(Project.objects.count(), 2)
        print("====create project===",Project.objects.all())
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Testing')

    def test_retrieve_project_list(self):
        self.client.post(reverse('audir:create_project'), {'project': 'Testing'})
        response = self.client.get(reverse('audir:project_list'))
        print("====project list===",Project.objects.all())
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Testing')

    def test_delete_project(self):
        print("====before delete proj===",Project.objects.all())
        response = self.client.post(reverse('audir:delete_selected_projects'), {'selected_projects': [self.project.id]}, follow=True)
        print("====after delete proj===",Project.objects.all())
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'Testing')

    #decorator
    @override_settings(MEDIA_ROOT=os.path.join(settings.BASE_DIR, 'test_media'))
    def test_upload_image_and_detection_module(self):
        #test if the image is uploaded and the results are saved after the detection module
        test_image_path = os.path.join(settings.MEDIA_ROOT, 'test_input.jpeg')

        with open(test_image_path, 'rb') as img:
            image_file = SimpleUploadedFile(
                name='test_input.jpeg',
                content=img.read(),
                content_type='image/jpeg'
            )

            response = self.client.post(
                reverse('audir:project_detail', args=[self.project.id]),
                data={'file': image_file},
                format='multipart'
            )
            print("====upload image===", Image.objects.all())
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Image.objects.count(), 1)
        self.assertEqual(Result.objects.count(), 1)

        result = Result.objects.first()
        print("====result from uploaded image===",result.length_index, result.length_ring,result.ratio,result.handedness)
        self.assertEqual(result.progression, 'done')
        self.assertIsNotNone(result.result_image)
        self.assertTrue(result.result_image.name.startswith('result/'))


    @override_settings(MEDIA_ROOT=os.path.join(settings.BASE_DIR, 'test_media'))
    def test_generate_csv(self):
        #export the results as a csv file and open the csv file to check if the result is exported correctly.
        test_image_path = os.path.join(settings.MEDIA_ROOT, 'test_input.jpeg')

        with open(test_image_path, 'rb') as img:
            image_file = SimpleUploadedFile(
                name='test_input.jpeg',
                content=img.read(),
                content_type='image/jpeg'
            )

            response = self.client.post(
                reverse('audir:project_detail', args=[self.project.id]),
                data={'file': image_file},
                format='multipart'
            )

            image = Image.objects.first()
            response = self.client.post(reverse('audir:generate_csv'),{'selected_images':[image.id]})
            print("====image to export===",Image.objects.all())
            self.assertEqual(response.status_code, 200)

            self.assertEqual(response['Content-Type'], 'text/csv')
            self.assertIn('attachment; filename="output.csv"', response['Content-Disposition'])

            content = response.content.decode('utf-8')
            csv_reader = csv.reader(io.StringIO(content))
            rows = list(csv_reader)
            filename = rows[1][0]
            indexfg=float(rows[1][1])
            ringfg=float(rows[1][2])
            digitratio=float(rows[1][3])

            self.assertEqual(rows[0], ['Filename', 'Index Finger(A)', 'Ring Finger(B)', 'Digit ratio(A/B)'])
            print("===read from csv===", filename, indexfg, ringfg, digitratio)
            self.assertIsNotNone(filename)
            self.assertEqual(indexfg, 82.0361) 
            self.assertEqual(ringfg, 83.5452)
            self.assertEqual(digitratio, 0.9819)

    @override_settings(MEDIA_ROOT=os.path.join(settings.BASE_DIR, 'test_media'))
    def test_delete_selected_images(self) :
        #delete the uploaded image
        test_image_path = os.path.join(settings.MEDIA_ROOT, 'test_input.jpeg')

        with open(test_image_path, 'rb') as img:
            image_file = SimpleUploadedFile(
                name='test_input.jpeg',
                content=img.read(),
                content_type='image/jpeg'
            )

            response = self.client.post(
                reverse('audir:project_detail', args=[self.project.id]),
                data={'file': image_file},
                format='multipart'
            )
            print("====before delete image===",Image.objects.all())
            #select the first image to delete
            uploaded_image = Image.objects.first()
            response = self.client.post(reverse('audir:delete_selected_images'), {'selected_images': [uploaded_image.id], 'project_id' : self.project.id}, follow=True)
            print("====after delete image===",Image.objects.all())
            self.assertEqual(response.status_code, 200)
            self.assertEqual(Image.objects.count(),0)
    
    @override_settings(MEDIA_ROOT=os.path.join(settings.BASE_DIR, 'test_media'))
    def test_result_detail(self):
        #check if the result detail page is created with the result id.
        test_image_path = os.path.join(settings.MEDIA_ROOT, 'test_input.jpeg')

        with open(test_image_path, 'rb') as img:
            image_file = SimpleUploadedFile(
                name='test_input.jpeg',
                content=img.read(),
                content_type='image/jpeg'
            )

            response = self.client.post(
                reverse('audir:project_detail', args=[self.project.id]),
                data={'file': image_file},
                format='multipart'
            )

            print("====result detail object===",Result.objects.all())
            result = Result.objects.first()
            url = reverse('audir:result_detail', args=[result.id])
            response = self.client.get(url, follow=True)
            print("====result detail url===",url, response)

            self.assertEqual(response.status_code, 200)
            self.assertIsNotNone(result.result_image)
