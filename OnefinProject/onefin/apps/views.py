import requests
from django.conf import settings
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from onefin.apps.models import Collections
from onefin.apps.serializers import RegistrationSerializer
from onefin.apps import serializers
from rest_framework import status, viewsets
from rest_framework.authtoken.models import Token
from rest_framework.mixins import (DestroyModelMixin, ListModelMixin,
                                   RetrieveModelMixin)
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework.views import APIView
import itertools


class RegistrationAPIViewset(viewsets.ViewSet):

    queryset = User.objects.all()
    serializer_class = RegistrationSerializer

    def create(self, request):
        user = request.data
        cur_user = authenticate(request=request, username=user.get(
            'username'), password=user.get('password'))
        if not cur_user:
            serializer = self.serializer_class(data=user)
            if serializer.is_valid():
                user_obj = serializer.save()
                token, created = Token.objects.get_or_create(user=user_obj)
                return Response(
                    {'token': token.key},
                    status=status.HTTP_201_CREATED
                )
            else:
                return Response(
                    {"is_success": False, "error": serializer.errors},
                    status=status.HTTP_400_BAD_REQUEST
                )
        else:
            token, created = Token.objects.get_or_create(user=cur_user)
            return Response({'token': token.key}, status=status.HTTP_200_OK)


class MovieAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):
        page = "?page=" + \
            request.GET.get('page') if request.GET.get('page') else ''
        cur_url = reverse('api:movie_api', request=request)
        response = requests.get('https://demo.credy.in/api/v1/maya/movies/' +
                                page,
                                auth=(settings.API_USERNAME,
                                      settings.API_PASSWORD)
                                )
        response_obj = response.json()
        response_obj['next'] = response_obj['next'].replace(
            'https://demo.credy.in/api/v1/maya/movies/', cur_url) \
            if 'next' in response_obj and response_obj['next'] \
            else None
        response_obj['previous'] = response_obj['previous'].replace(
            'https://demo.credy.in/api/v1/maya/movies/', cur_url) \
            if 'previous' in response_obj and response_obj['previous'] \
            else None
        return Response(response_obj)


class CollectionsViewSet(
    viewsets.GenericViewSet, RetrieveModelMixin,
    DestroyModelMixin, ListModelMixin
):

    permission_classes = [IsAuthenticated]
    serializer_class = serializers.CollectionSerializer

    def get_queryset(self):
        user = self.request.user
        return Collections.objects.filter(user=user)

    def get_serializer(self, *args, **kwargs):
        if self.action == 'list':
            return serializers.ListCollectionSerializer(*args, **kwargs)
        return serializers.CollectionSerializer(*args, **kwargs)

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        serializer = self.get_serializer(queryset, many=True)

        all_generes = {}

        serializer_with_movies = self.serializer_class(queryset, many=True)

        for collection in serializer_with_movies.data:
            for movie in collection['movies']:
                for genre in movie['genres'].split(','):
                    if genre in all_generes:
                        all_generes[genre] += 1
                    else:
                        all_generes[genre] = 1

        sorted_generes = dict(
            sorted(all_generes.items(),
                   key=lambda item: item[1], reverse=True))

        top_three_generes = dict(itertools.islice(sorted_generes.items(), 3))

        favourite_genres = ", ".join(top_three_generes.keys())

        return Response({
            "is_success": True,
            "data": {
                "collections": serializer.data,
                "favourite_genres": favourite_genres
            }
        })

    def create(self, request):
        collection = self.get_serializer(data=request.data)
        collection.is_valid(raise_exception=True)
        created_collection = collection.save(user=request.user)

        return Response({'collection_uuid': created_collection.uuid})

    def update(self, request,  *args, **kwargs):
        try:
            collection = self.get_object()
            data_to_update = request.data
            updated_collection = self.get_serializer(
                collection, data=data_to_update, partial=True)
            updated_collection.is_valid(raise_exception=True)
            updated_collection.save()
            return Response(updated_collection.data,
                            status=status.HTTP_202_ACCEPTED)
        except Exception as e:
            return Response({'is_success': False, 'error': e.args[0]},
                            status=status.HTTP_400_BAD_REQUEST)
