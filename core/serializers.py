from rest_framework import serializers
from django.contrib.auth.hashers import make_password
from .models import Account, Family, Volunteer
from .models import ReportCase, ReportMedia


class FamilySerializer(serializers.ModelSerializer):
    class Meta:
        model = Family
        fields = "__all__"
        read_only_fields = ["family_id", "account"]

class VolunteerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Volunteer
        fields = "__all__"
        read_only_fields = ["volunteer_id", "account"]

class AccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = Account
        fields = [
            "account_id",
            "username",
            "full_name",
            "email",
            "password",
            "role",
            "created_at",
        ]
        extra_kwargs = {
            "password": {"write_only": True},
            "role": {"read_only": True},
        }

    def create(self, validated_data):
        password = validated_data.pop("password", None)
        user = super().create(validated_data)
        if password:
            user.set_password(password)
        user.is_active = False 
        user.save()
        return user


class ReportMediaSerializer(serializers.ModelSerializer):
    file_url = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = ReportMedia
        fields = ["media_id", "report", "file", "file_url", "file_type", "uploaded_at"]
        extra_kwargs = {
            "file": {"write_only": True}  # we accept uploads but don’t return the raw path
        }

    def get_file_url(self, obj):
        request = self.context.get("request")
        if obj.file and hasattr(obj.file, "url"):
            return request.build_absolute_uri(obj.file.url) if request else obj.file.url
        return None


class ReportSerializer(serializers.ModelSerializer):
    media = ReportMediaSerializer(many=True, read_only=True)
    reporter = AccountSerializer(read_only=True)

    class Meta:
        model = ReportCase
        fields = "__all__"
        read_only_fields = ["report_id", "reporter", "created_at", "media"]

    def create(self, validated_data):
        user = self.context["request"].user
        validated_data["reporter"] = user
        return super().create(validated_data)
