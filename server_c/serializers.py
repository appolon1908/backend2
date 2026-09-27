from rest_framework import serializers

from .models import MarketplaceCategory, MarketplaceProduct, MarketplacePublisher, ProspectList, SalesCompany, SalesContact


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = MarketplaceCategory
        fields = "__all__"


class PublisherSerializer(serializers.ModelSerializer):
    class Meta:
        model = MarketplacePublisher
        fields = ("code", "display_name", "status")


class ProductSerializer(serializers.ModelSerializer):
    publisher = serializers.SlugRelatedField(read_only=True, slug_field="code")
    category = serializers.SlugRelatedField(read_only=True, slug_field="code")

    class Meta:
        model = MarketplaceProduct
        fields = "__all__"


class SalesCompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = SalesCompany
        exclude = ("id",)


class SalesContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = SalesContact
        exclude = ("id",)


class ProspectListSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProspectList
        exclude = ("id",)
