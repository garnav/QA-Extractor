from rest_framework import serializers
from .models import Configurations, toConvert, Converted

class ConfigurationsSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Configurations
        fields = ('id', 'name', 'input_type', 'description')
        
class toConvertSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = toConvert
        fields = ('id', 'name', 'extension', 'organization')

class chatAnswerSerializer(serializers.BaseSerializer):
    def to_representation(self, answer):
        return answer
        
