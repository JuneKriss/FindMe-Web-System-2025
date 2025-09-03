from rest_framework import serializers
from django.contrib.auth.hashers import make_password
from .models import Account
from .models import ReportCase



class AccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = Account
        fields = ['account_id', 'username', 'email', 'password', 'role', 'created_at']
        extra_kwargs = {
            'password': {'write_only': True}
        }

    def create(self, validated_data):
        password = validated_data.pop('password')
        account = Account(**validated_data)
        account.password = make_password(password)
        account.save()
        return account
    
class ReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReportCase
        fields = "__all__"
        read_only_fields = ["report_id", "reporter", "created_at"]

        def create(self, validated_data):
            # Automatically assign the logged-in user as reporter
            user = self.context["request"].user
            validated_data["reporter"] = user
            return super().create(validated_data)