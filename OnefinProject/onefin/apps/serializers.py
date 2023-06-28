from django.contrib.auth.models import User
from onefin.apps.models import Collections
from rest_framework import serializers


class RegistrationSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = ["username", "password"]

    def create(self, validated_data):
        # Use the `create_user` method we wrote earlier to create a new user.
        user = User.objects.create_user(**validated_data)
        user.set_password(validated_data.get('password'))
        return user


class CollectionSerializer(serializers.ModelSerializer):

    class Meta:
        model = Collections
        exclude = ['user']

    def create(self, validated_data):
        return Collections.objects.create(**validated_data)


class ListCollectionSerializer(serializers.ModelSerializer):

    class Meta:
        model = Collections
        exclude = ['user', 'movies', ]
