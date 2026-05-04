from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import JsonResponse
from accounts.models import Device
from .models import PrivacyBudget


def is_admin(user):
    return user.is_superuser or getattr(user, 'user_type', '') == 'admin'


@login_required
def privacy_overview(request):
    # Always show all devices and auto-create missing budgets for new devices.
    all_devices = Device.objects.all()
    for device in all_devices:
        if not PrivacyBudget.objects.filter(device=device).exists():
            PrivacyBudget.objects.create(device=device)

    budgets = PrivacyBudget.objects.select_related('device', 'device__user').order_by('device__device_name')
    return render(request, 'privacy/overview.html', {'budgets': budgets})


@login_required
def privacy_budgets_api(request):
    """Return all privacy budgets for live table refresh."""
    all_devices = Device.objects.all()
    for device in all_devices:
        if not PrivacyBudget.objects.filter(device=device).exists():
            PrivacyBudget.objects.create(device=device)

    budgets = PrivacyBudget.objects.select_related('device', 'device__user').order_by('device__device_name')
    rows = []
    for b in budgets:
        query_pct = int((b.used_query_epsilon / b.total_query_epsilon) * 100) if b.total_query_epsilon else 0
        grad_pct = int((b.used_gradient_epsilon / b.total_gradient_epsilon) * 100) if b.total_gradient_epsilon else 0
        rows.append({
            'device_id': str(b.device.device_id),
            'device_name': b.device.device_name,
            'owner': b.device.user.username if b.device.user else '-',
            'query_used': f'{b.used_query_epsilon:.3f}',
            'query_total': f'{b.total_query_epsilon:.3f}',
            'query_pct': max(0, min(query_pct, 100)),
            'grad_used': f'{b.used_gradient_epsilon:.3f}',
            'grad_total': f'{b.total_gradient_epsilon:.3f}',
            'grad_pct': max(0, min(grad_pct, 100)),
            'delta': f'{b.delta:g}',
        })
    return JsonResponse({'budgets': rows})


@login_required
def device_privacy_detail(request, device_id):
    device = get_object_or_404(Device, device_id=device_id)
    budget, _ = PrivacyBudget.objects.get_or_create(device=device)
    return render(request, 'privacy/detail.html', {'device': device, 'budget': budget})


@user_passes_test(is_admin)
def reset_device_privacy(request, device_id):
    device = get_object_or_404(Device, device_id=device_id)
    budget, _ = PrivacyBudget.objects.get_or_create(device=device)
    budget.reset_budgets()
    return render(request, 'privacy/reset_result.html', {'device': device, 'budget': budget})
