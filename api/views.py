from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from accounts.models import Device
from federated_learning.models import FLRound, ModelUpdate
from .serializers import DeviceSerializer, FLRoundSerializer, ModelUpdateSerializer
import json


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_devices(request):
    devices = Device.objects.filter(user=request.user)
    serializer = DeviceSerializer(devices, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_rounds(request):
    # Get limit from query params (default 50, max 100)
    limit = min(int(request.GET.get('limit', 50)), 100)
    offset = int(request.GET.get('offset', 0))
    
    rounds = FLRound.objects.all().order_by('-round_number')[offset:offset+limit]
    total = FLRound.objects.count()
    
    serializer = FLRoundSerializer(rounds, many=True)
    return Response({
        'total': total,
        'count': len(serializer.data),
        'offset': offset,
        'limit': limit,
        'results': serializer.data
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_upload_update(request):
    """
    External IIoT device can POST:
    {
      "round_id": "...",
      "device_id": "...",
      "model_weights": {...},
      "local_accuracy": 90.0,
      "local_loss": 0.3
    }
    """
    data = request.data
    try:
        fl_round = FLRound.objects.get(round_id=data.get('round_id'))
        device = Device.objects.get(device_id=data.get('device_id'))
    except (FLRound.DoesNotExist, Device.DoesNotExist):
        return Response({'error': 'Invalid round or device'}, status=400)

    mu = ModelUpdate.objects.create(
        fl_round=fl_round,
        device=device,
        model_weights=json.dumps(data.get('model_weights', {})),
        local_accuracy=float(data.get('local_accuracy', 0.0)),
        local_loss=float(data.get('local_loss', 0.0)),
        training_samples=int(data.get('training_samples', 100)),
    )

    serializer = ModelUpdateSerializer(mu)
    return Response(serializer.data, status=201)
