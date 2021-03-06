from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APIClient


#importar modelos que estan en la api core
from core.models import Tag, Recipe
#importar serializador del tag
from recipe.serializers import TagSerializer

TAGS_URL = reverse('recipe:tag-list')

class PublicTagsApiTests(TestCase):
    '''Probar los API tags disponibles pulicamente'''

    def setUp(self):
        self.client = APIClient()

    def test_login_required(self):
        '''Prueba que login sea requerido para obtener los tags'''
        res = self.client.get(TAGS_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

class PrivateTagsApiTest(TestCase):
    '''Probar los API tags disponibles privados'''
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            'prueba@gmail.com',
            'password'
        )
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_retrieve_tags(self):
        '''Para obtener tags'''
        Tag.objects.create(user=self.user,name='Meat')
        Tag.objects.create(user=self.user,name='Banana')
        res = self.client.get(TAGS_URL)

        tags = Tag.objects.all().order_by('-name')
        serializer = TagSerializer(tags,many=True)
        self.assertEqual(res.status_code,status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_tags_limited_to_user(self):
        '''Probar que los tags retornados sean del usuario'''
        user2 = get_user_model().objects.create_user(
            'prueba2@gmail.com',
            'testpass'
        )
        Tag.objects.create(user=user2,name='Raspberry')
        tag = Tag.objects.create(user=self.user,name='Comfort Food')
        #request
        res = self.client.get(TAGS_URL)

        self.assertEqual(res.status_code,status.HTTP_200_OK)
        self.assertEqual(len(res.data),1)
        self.assertEqual(res.data[0]['name'], tag.name)

    def test_create_tag_succesful(self):
        '''Prueba creando nuevo tag'''
        payload = {'name':'Simple'}
        self.client.post(TAGS_URL,payload)

        exists = Tag.objects.filter(
            user = self.user,
            name=payload['name']
        ).exists()
        self.assertTrue(exists)

    def test_create_tag_invalid(self):
        payload = {'name':''}
        res = self.client.post(TAGS_URL,payload)
        self.assertEqual(res.status_code,status.HTTP_400_BAD_REQUEST)

    def test_create_tag_invalid(self):
        '''Prueba crear un nuevo tag con payload invalido'''
        payload = {'name':''}
        res = self.client.post(TAGS_URL,payload)

        self.assertEqual(res.status_code,status.HTTP_400_BAD_REQUEST)

    def test_retrieve_tags_assigned_to_recipes(self):
        '''prueba filtrando tags basrado en receta'''
        tag1 = Tag.objects.create(user=self.user,name='Breakfast')
        tag2 = Tag.objects.create(user=self.user,name='Lunch')
        recipe = Recipe.objects.create(
            title='Coriander eggs on toast',
            time_minutes=10,
            price=5.00,
            user = self.user,
        )
        recipe.tags.add(tag1)

        res = self.client.get(TAGS_URL,{'assigned_only':1})

        serializer1= TagSerializer(tag1)
        serializer2= TagSerializer(tag2)
        self.assertIn(serializer1.data,res.data)
        self.assertNotIn(serializer2.data,res.data)

    def test_retrieve_tags_assigned_to_unique(self):
        '''Prueba filtro tags asignado por items unico'''
        tag = Tag.objects.create(user=self.user,name='Breakfast')
        recipe1 = Recipe.objects.create(
            title='Pancakes',
            time_minutes=5,
            price=3.00,
            user = self.user,
        )
        recipe1.tags.add(tag)
        recipe2 = Recipe.objects.create(
            title='Porridge',
            time_minutes=3,
            price=2.00,
            user = self.user,
        )
        recipe2.tags.add(tag)

        res = self.client.get(TAGS_URL,{'assigned_only':1})

        self.assertEqual(len(res.data),1)
