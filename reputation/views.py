from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from accounts.models import Device
from .models import ReputationScore, ReputationHistory
from .reputation_engine import ReputationEngine

engine = ReputationEngine()


def is_admin(user):
    return user.is_superuser or getattr(user, 'user_type', '') == 'admin'


@login_required
def reputation_overview(request):
    # Show one clear latest score per device for all devices.
    all_devices = Device.objects.select_related('user').order_by('device_name')

    score_rows = []
    for device in all_devices:
        if not ReputationScore.objects.filter(device=device).exists():
            # Use engine to calculate dynamic reputation and confidence
            latest_score = engine.update_reputation(device=device, round_number=0, reason="Initial device setup")
        else:
            latest_score = ReputationScore.objects.filter(device=device).order_by('-timestamp').first()

        score_rows.append({
            'device': device,
            'score_obj': latest_score,
            'score': latest_score.score if latest_score else 0.5,
            'confidence': latest_score.confidence if latest_score else 0.5,
            'round_number': latest_score.round_number if latest_score else 0,
            'timestamp': latest_score.timestamp if latest_score else None,
        })

    score_rows.sort(key=lambda row: row['score'], reverse=True)

    high_count = sum(1 for row in score_rows if row['score'] >= 0.7)
    medium_count = sum(1 for row in score_rows if 0.5 <= row['score'] < 0.7)
    low_count = sum(1 for row in score_rows if row['score'] < 0.5)

    return render(request, 'reputation/overview.html', {
        'score_rows': score_rows,
        'high_count': high_count,
        'medium_count': medium_count,
        'low_count': low_count,
    })


@login_required
def device_reputation_detail(request, device_id):
    device = get_object_or_404(Device, device_id=device_id)
    scores = ReputationScore.objects.filter(device=device).order_by('-timestamp')[:20]
    history = ReputationHistory.objects.filter(device=device).order_by('-created_at')[:20]
    return render(request, 'reputation/detail.html', {
        'device': device,
        'scores': scores,
        'history': history,
    })


@user_passes_test(is_admin)
def recompute_reputation(request, device_id):
    device = get_object_or_404(Device, device_id=device_id)
    rep = engine.update_reputation(device=device, round_number=0, reason="Manual recompute")
    return render(request, 'reputation/recompute_result.html', {'device': device, 'reputation': rep})
