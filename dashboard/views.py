from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Q
from django.core.management import call_command
from accounts.models import Device, User
from federated_learning.models import FLRound, ModelUpdate, GlobalModel
from blockchain.models import Block
from reputation.models import ReputationScore
from privacy.models import PrivacyBudget
from security.models import AttackLog
import io


def is_admin(user):
    return user.is_superuser or user.is_staff or getattr(user, 'user_type', '') == 'admin'


def admin_required(view_func):
    """Decorator to ensure user is admin"""
    def wrapper(request, *args, **kwargs):
        if not is_admin(request.user):
            messages.error(request, 'Access denied. Admin privileges required.')
            return redirect('dashboard:user_dashboard')
        return view_func(request, *args, **kwargs)
    return login_required(wrapper)


@login_required
def user_dashboard(request):
    if is_admin(request.user):
        return redirect('dashboard:admin_dashboard')

    # Show all devices in system for complete visibility
    devices = Device.objects.all().select_related('user')
    
    # Auto-create missing records for current user's devices only
    user_devices = Device.objects.filter(user=request.user)
    for device in user_devices:
        # Only create if doesn't exist
        if not PrivacyBudget.objects.filter(device=device).exists():
            PrivacyBudget.objects.create(device=device)
        # Only create if no reputation score exists at all
        if not ReputationScore.objects.filter(device=device).exists():
            ReputationScore.objects.create(
                device=device,
                round_number=0,
                score=0.5,
                confidence=0.5
            )
    
    rounds = FLRound.objects.all().order_by('-round_number')[:5]
    latest_round = rounds[0] if rounds else None
    # Show all model updates in system for complete visibility
    updates = ModelUpdate.objects.all().select_related(
        'device', 'device__user', 'fl_round'
    ).order_by('-uploaded_at')[:20]
    
    # Attach latest reputation to each device for easy template access
    for d in devices:
        latest_rep = ReputationScore.objects.filter(device=d).order_by('-timestamp').first()
        d.latest_reputation = latest_rep.score if latest_rep else 0.5
    
    context = {
        'devices': devices,
        'rounds': rounds,
        'latest_round': latest_round,
        'updates': updates,
    }
    return render(request, 'dashboard/user/dashboard.html', context)


@login_required
def admin_dashboard(request):
    if not is_admin(request.user):
        return user_dashboard(request)
    
    # Auto-create missing records for all devices
    all_devices = Device.objects.all()
    for device in all_devices:
        PrivacyBudget.objects.get_or_create(device=device)
        # Only create if no reputation score exists at all
        if not ReputationScore.objects.filter(device=device).exists():
            ReputationScore.objects.create(
                device=device,
                round_number=0,
                score=0.5,
                confidence=0.5
            )
    
    device_count = Device.objects.count()
    active_devices = Device.objects.filter(status='active').count()
    blocked_devices = Device.objects.filter(status='blocked').count()
    
    rounds = FLRound.objects.all().order_by('-round_number')[:10]
    blocks = Block.objects.all().order_by('-index')[:10]
    attacks = AttackLog.objects.all().order_by('-created_at')[:10]
    
    top_reputation = ReputationScore.objects.select_related('device').order_by('-score')[:10]
    
    # Get user statistics
    user_count = User.objects.count()
    admin_count = User.objects.filter(Q(user_type='admin') | Q(is_superuser=True)).count()
    active_users = User.objects.filter(is_active=True).count()
    
    context = {
        'device_count': device_count,
        'active_devices': active_devices,
        'blocked_devices': blocked_devices,
        'user_count': user_count,
        'admin_count': admin_count,
        'active_users': active_users,
        'rounds': rounds,
        'blocks': blocks,
        'attacks': attacks,
        'top_reputation': top_reputation,
    }
    return render(request, 'dashboard/admin/dashboard.html', context)


@admin_required
def sync_devices_view(request):
    """Admin: Trigger device sync to update all reputation, malicious detection, etc."""
    try:
        # Capture command output
        out = io.StringIO()
        call_command('sync_devices', '--update-reputation', stdout=out)
        
        output = out.getvalue()
        # Extract summary from output
        if 'Sync complete!' in output:
            lines = output.split('\n')
            summary_lines = [l for l in lines if 'created:' in l or 'updated:' in l]
            summary = ' | '.join(summary_lines)
            messages.success(request, f'Device sync completed! {summary}')
        else:
            messages.success(request, 'Device sync completed successfully!')
    except Exception as e:
        messages.error(request, f'Sync failed: {str(e)}')
    
    return redirect('dashboard:admin_dashboard')


# User Management Views
@admin_required
def user_management_list(request):
    """List all users for admin management"""
    search_query = request.GET.get('search', '')
    user_type_filter = request.GET.get('type', '')
    status_filter = request.GET.get('status', '')
    
    users = User.objects.all().annotate(
        device_count=Count('devices')
    ).order_by('-date_joined')
    
    # Apply filters
    if search_query:
        users = users.filter(
            Q(username__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query)
        )
    
    if user_type_filter:
        users = users.filter(user_type=user_type_filter)
    
    if status_filter == 'active':
        users = users.filter(is_active=True)
    elif status_filter == 'inactive':
        users = users.filter(is_active=False)
    
    context = {
        'users': users,
        'search_query': search_query,
        'user_type_filter': user_type_filter,
        'status_filter': status_filter,
    }
    return render(request, 'dashboard/admin/user_management.html', context)


@admin_required
def user_detail(request, user_id):
    """View detailed information about a user"""
    user = get_object_or_404(User, id=user_id)
    devices = Device.objects.filter(user=user).annotate(
        update_count=Count('modelupdate')
    )
    
    context = {
        'viewed_user': user,
        'devices': devices,
    }
    return render(request, 'dashboard/admin/user_detail.html', context)


@admin_required
def user_edit(request, user_id):
    """Edit user information"""
    user = get_object_or_404(User, id=user_id)
    
    if request.method == 'POST':
        # Prevent self-demotion
        if user.id == request.user.id and request.POST.get('user_type') != 'admin':
            messages.error(request, 'You cannot change your own admin status.')
            return redirect('dashboard:user_detail', user_id=user.id)
        
        # Update user fields
        user.email = request.POST.get('email', user.email)
        user.first_name = request.POST.get('first_name', user.first_name)
        user.last_name = request.POST.get('last_name', user.last_name)
        user.user_type = request.POST.get('user_type', user.user_type)
        user.organization = request.POST.get('organization', user.organization)
        user.phone_number = request.POST.get('phone_number', user.phone_number)
        
        # Handle active status
        is_active = request.POST.get('is_active') == 'on'
        user.is_active = is_active
        
        # Handle verified status
        is_verified = request.POST.get('is_verified') == 'on'
        user.is_verified = is_verified
        
        user.save()
        messages.success(request, f'User {user.username} updated successfully.')
        return redirect('dashboard:user_detail', user_id=user.id)
    
    context = {'viewed_user': user}
    return render(request, 'dashboard/admin/user_edit.html', context)


@admin_required
def user_toggle_status(request, user_id):
    """Toggle user active/inactive status"""
    user = get_object_or_404(User, id=user_id)
    
    # Prevent self-deactivation
    if user.id == request.user.id:
        messages.error(request, 'You cannot deactivate your own account.')
        return redirect('dashboard:user_management')
    
    user.is_active = not user.is_active
    user.save()
    
    status = 'activated' if user.is_active else 'deactivated'
    messages.success(request, f'User {user.username} has been {status}.')
    return redirect('dashboard:user_management')


@admin_required
def user_delete(request, user_id):
    """Delete a user (soft delete by deactivating)"""
    user = get_object_or_404(User, id=user_id)
    
    # Prevent self-deletion
    if user.id == request.user.id:
        messages.error(request, 'You cannot delete your own account.')
        return redirect('dashboard:user_management')
    
    if request.method == 'POST':
        username = user.username
        user.is_active = False
        user.save()
        messages.success(request, f'User {username} has been deactivated.')
        return redirect('dashboard:user_management')
    
    context = {'viewed_user': user}
    return render(request, 'dashboard/admin/user_delete_confirm.html', context)
