from rest_framework.viewsets import ViewSet
from cms.models import HeaderTitle
from cms.serializers import HeaderTitleSerializer

from rest_framework.response import Response
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema




class HeaderTitleViewSet(ViewSet):
    
    def get_queryset(self):
        return HeaderTitle.objects.order_by('-id')[:1]
    
    @swagger_auto_schema(
        operation_description="Home page header title",
        operation_summary="Home page header title",
        tags=["HeaderTitle"],
    )
    def list(self, request):
        title = HeaderTitle.objects.order_by('-id')
        return Response(HeaderTitleSerializer(title, many=True).data, status=status.HTTP_200_OK)
        
    @swagger_auto_schema(
        operation_description="Home page header title form",
        operation_summary="Home page header title form",
        tags=["HeaderTitle"],
        request_body=HeaderTitleSerializer
    )
    def create(self, request):
        serializer = HeaderTitleSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
   