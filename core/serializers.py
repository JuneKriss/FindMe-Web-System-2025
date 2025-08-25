from rest_framework import serializers
from .models import Account
from django.contrib.auth.hashers import make_password

class AccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = Account
        fields = "__all__"

    def create(self, validated_data):
        password = validated_data.pop('password')
        account = Account(**validated_data)
        account.password = make_password(password)  # hash
        account.save()
        return account