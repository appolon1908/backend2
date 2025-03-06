from rest_framework import serializers



class PaymentSerializer(serializers.Serializer):
    email = serializers.EmailField()
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    description = serializers.CharField(required=False)
    name = serializers.CharField()
    # stripe_token = serializers.CharField()