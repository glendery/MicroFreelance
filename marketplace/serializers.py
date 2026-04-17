from rest_framework import serializers
from .models import Project, Category, User

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'role', 'balance', 'avatar']

class ProjectSerializer(serializers.ModelSerializer):
    client = UserSerializer(read_only=True)
    freelancer = UserSerializer(read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)

    class Meta:
        model = Project
        fields = '__all__'
