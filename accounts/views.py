from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views import View
from django.utils.decorators import method_decorator
from django.db import transaction
from django.utils import timezone
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from .models import User, Device, DeviceMetrics
from .forms import UserRegistrationForm, UserLoginForm, DeviceRegistrationForm
import uuid
import random
import hashlib
import json

def generate_mac_address():
    """Generate random MAC address"""
    mac = [0x00, 0x16, 0x3e,
           random.randint(0x00, 0x7f),
           random.randint(0x00, 0xff),
           random.randint(0x00, 0xff)]
    return ':'.join(map(lambda x: "%02x" % x, mac))


def initialize_device_records(device):
    """Create baseline records so a new device appears across all modules immediately."""
    from reputation.models import ReputationScore
    from privacy.models import PrivacyBudget
    from security.models import AnomalyDetectionResult
    from blockchain.models import Transaction as BlockchainTransaction
    from federated_learning.models import FLRound
    from datetime import timedelta

    # Create reputation score only if none exists
    if not ReputationScore.objects.filter(device=device).exists():
        ReputationScore.objects.create(
            device=device,
            round_number=0,
            score=0.5,
            confidence=0.5
        )

    PrivacyBudget.objects.get_or_create(device=device)

    # Create anomaly detection record only if none exists for round 0
    if not AnomalyDetectionResult.objects.filter(device=device, fl_round_number=0).exists():
        AnomalyDetectionResult.objects.create(
            device=device,
            fl_round_number=0,
            gradient_norm=0.0,
            z_score=0.0,
            is_anomalous=bool(device.is_malicious)
        )

    tx_hash = hashlib.sha256(
        f"device-register:{device.device_id}:{timezone.now().timestamp()}".encode('utf-8')
    ).hexdigest()
    BlockchainTransaction.objects.create(
        tx_hash=tx_hash,
        sender='SYSTEM',
        recipient='FLNetwork',
        data=json.dumps({
            'type': 'DEVICE_REGISTER',
            'device_id': str(device.device_id),
            'device_name': device.device_name,
            'is_malicious': bool(device.is_malicious),
        }),
        timestamp=timezone.now(),
        sender_device=device,
    )

    # Create initial metrics for new device (5 records)
    if not DeviceMetrics.objects.filter(device=device).exists():
        now = timezone.now()
        for i in range(5, 0, -1):  # Create 5 metrics going back in time
            DeviceMetrics.objects.create(
                device=device,
                cpu_usage=random.uniform(20, 60),
                memory_usage=random.uniform(30, 70),
                network_latency=random.uniform(10, 50),
                battery_level=random.uniform(70, 100),
                data_size=random.randint(1000000, 5000000),
                uptime=random.randint(3600, 21600),
                timestamp=now - timedelta(minutes=i)
            )

    in_progress_rounds = FLRound.objects.filter(status='in_progress')
    for fl_round in in_progress_rounds:
        if fl_round.current_participants < fl_round.max_participants:
            fl_round.current_participants += 1
            fl_round.save(update_fields=['current_participants'])


class UserRegistrationView(View):
    """User Registration View"""
    
    def get(self, request):
        if request.user.is_authenticated:
            return redirect('dashboard:user_dashboard')
        form = UserRegistrationForm()
        return render(request, 'accounts/register.html', {'form': form})
    
    def post(self, request):
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, 'Registration successful! Please login.')
            return redirect('accounts:login')
        return render(request, 'accounts/register.html', {'form': form})


class UserLoginView(View):
    """User Login View"""
    
    def get(self, request):
        if request.user.is_authenticated:
            if request.user.is_superuser or request.user.is_staff or getattr(request.user, 'user_type', '') == 'admin':
                return redirect('dashboard:admin_dashboard')
            return redirect('dashboard:user_dashboard')
        form = UserLoginForm()
        return render(request, 'accounts/login.html', {'form': form})
    
    def post(self, request):
        form = UserLoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f'Welcome back, {user.username}!')
                if user.is_superuser or user.is_staff or getattr(user, 'user_type', '') == 'admin':
                    return redirect('dashboard:admin_dashboard')
                return redirect('dashboard:user_dashboard')
            else:
                messages.error(request, 'Invalid username or password.')
        return render(request, 'accounts/login.html', {'form': form})


@login_required
def user_logout(request):
    """User Logout"""
    logout(request)
    messages.info(request, 'You have been logged out successfully.')
    return redirect('accounts:login')


@login_required
def profile_view(request):
    """User Profile View"""
    devices = Device.objects.all().select_related('user')
    context = {
        'user': request.user,
        'devices': devices,
        'device_count': devices.count(),
        'active_devices': devices.filter(status='active').count(),
    }
    return render(request, 'accounts/profile.html', context)


@login_required
def device_list_view(request):
    """List all devices in the system"""
    devices = Device.objects.all().select_related('user').order_by('device_name')
    context = {'devices': devices}
    return render(request, 'accounts/device_list.html', context)


@login_required
def device_register_view(request):
    """Register new device"""
    if request.method == 'POST':
        form = DeviceRegistrationForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                device = form.save(commit=False)
                device.user = request.user
                device.mac_address = generate_mac_address()
                device.status = 'active'
                device.save()

                initialize_device_records(device)

            malicious_label = 'Yes' if device.is_malicious else 'No'
            messages.success(
                request,
                f'Device "{device.device_name}" registered successfully! Malicious: {malicious_label}.'
            )
            return redirect('accounts:device_list')
    else:
        form = DeviceRegistrationForm()
    
    return render(request, 'accounts/device_register.html', {'form': form})


@login_required
def device_detail_view(request, device_id):
    """Device detail view - show all devices, not just user's devices"""
    device = get_object_or_404(Device, device_id=device_id)
    metrics = DeviceMetrics.objects.filter(device=device).order_by('-timestamp')[:10]
    
    context = {
        'device': device,
        'metrics': metrics,
        'reputation_score': device.get_reputation_score(),
    }
    return render(request, 'accounts/device_detail.html', context)


@login_required
def device_delete_view(request, device_id):
    """Delete device"""
    device = get_object_or_404(Device, device_id=device_id, user=request.user)
    if request.method == 'POST':
        device_name = device.device_name
        device.delete()
        messages.success(request, f'Device "{device_name}" deleted successfully!')
        return redirect('accounts:device_list')
    
    return render(request, 'accounts/device_confirm_delete.html', {'device': device})


@login_required
@require_http_methods(["GET"])
def device_metrics_api(request, device_id):
    """Return recent metrics for a device as JSON for live UI refresh."""
    device = get_object_or_404(Device, device_id=device_id)
    metrics = DeviceMetrics.objects.filter(device=device).order_by('-timestamp')[:20]
    
    data = []
    for m in metrics:
        data.append({
            'timestamp': timezone.localtime(m.timestamp).strftime('%Y-%m-%d %H:%M:%S'),
            'cpu_usage': float(m.cpu_usage),
            'memory_usage': float(m.memory_usage),
            'network_latency': float(m.network_latency),
            'battery_level': float(m.battery_level),
            'uptime': m.uptime,
            'data_size': m.data_size,
        })
    
    return JsonResponse({'metrics': data})
