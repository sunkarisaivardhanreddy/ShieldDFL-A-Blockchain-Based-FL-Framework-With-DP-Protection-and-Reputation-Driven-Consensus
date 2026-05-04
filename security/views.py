from django.shortcuts import render
from django.contrib.auth.decorators import login_required, user_passes_test
from .models import AttackLog, AnomalyDetectionResult


def is_admin(user):
    return user.is_superuser or getattr(user, 'user_type', '') == 'admin'


@user_passes_test(is_admin)
def security_overview(request):
    # Auto-create missing anomaly detection records for existing devices
    from accounts.models import Device
    all_devices = Device.objects.all()
    for device in all_devices:
        # Only create if no record exists for this device
        if not AnomalyDetectionResult.objects.filter(device=device, fl_round_number=0).exists():
            AnomalyDetectionResult.objects.create(
                device=device,
                fl_round_number=0,
                gradient_norm=0.0,
                z_score=0.0,
                is_anomalous=device.is_malicious
            )
    
    attacks = AttackLog.objects.all().select_related('device')[:50]
    anomalies = AnomalyDetectionResult.objects.all().select_related('device')[:50]
    return render(request, 'security/overview.html', {'attacks': attacks, 'anomalies': anomalies})


@user_passes_test(is_admin)
def sar_logs(request):
    logs = AttackLog.objects.filter(attack_type='SAR').select_related('device')
    return render(request, 'security/sar_logs.html', {'logs': logs})


@user_passes_test(is_admin)
def basr_logs(request):
    logs = AttackLog.objects.filter(attack_type='BASR').select_related('device')
    return render(request, 'security/basr_logs.html', {'logs': logs})
