from rest_framework import serializers
from accounts.models import Device
from federated_learning.models import FLRound, ModelUpdate


class DeviceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Device
        fields = ['device_id', 'device_name', 'device_type', 'status', 'is_malicious']


class FLRoundSerializer(serializers.ModelSerializer):
    class Meta:
        model = FLRound
        fields = ['round_id', 'round_number', 'status', 'global_model_accuracy', 'global_model_loss']


class ModelUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ModelUpdate
        fields = ['update_id', 'fl_round', 'device', 'local_accuracy', 'local_loss', 'is_malicious']
