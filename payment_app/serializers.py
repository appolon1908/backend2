from rest_framework import serializers


class PaymentSerializer(serializers.Serializer):
    email = serializers.EmailField()
    product_code = serializers.CharField(max_length=128)
    description = serializers.CharField(required=False)
    name = serializers.CharField(max_length=256)

    def validate(self, attrs):
        if "amount" in self.initial_data:
            raise serializers.ValidationError(
                {"amount": "Payment amount is server-authoritative and must not be supplied by the client."}
            )
        return attrs
