from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.conf import settings
from django.utils import timezone
from accounts.models import Device
from .models import FLRound, ModelUpdate, GlobalModel, TrainingMetrics
from .fl_engine import FederatedAveraging, calculate_gradient_norm
from privacy.models import PrivacyBudget
from privacy.dp_mechanisms import apply_dp_to_gradients
from security.attack_detector import run_attack_detection
from security.attack_simulator import simulate_sar_attack, simulate_basr_attack
from reputation.reputation_engine import ReputationEngine
from blockchain.blockchain_core import Transaction as CoreTransaction
from blockchain.models import BlockchainLedger
from blockchain.views import blockchain_instance
import json
import random

rep_engine = ReputationEngine()


def is_admin(user):
    return user.is_superuser or getattr(user, 'user_type', '') == 'admin'


@login_required
def round_list(request):
    from django.core.paginator import Paginator
    
    # Get all rounds
    all_rounds = FLRound.objects.all().order_by('-round_number')
    
    # Paginate: 20 rounds per page
    paginator = Paginator(all_rounds, 20)
    page_number = request.GET.get('page', 1)
    rounds_page = paginator.get_page(page_number)
    
    if is_admin(request.user):
        new_devices = Device.objects.select_related('user').order_by('-created_at')[:10]
    else:
        new_devices = Device.objects.filter(user=request.user).order_by('-created_at')[:10]
    
    context = {
        'rounds': rounds_page,
        'new_devices': new_devices,
        'total_rounds': paginator.count,
        'has_other_pages': rounds_page.has_other_pages(),
    }
    return render(request, 'fl/round_list.html', context)


@login_required
def round_detail(request, round_id):
    from django.core.paginator import Paginator
    
    fl_round = get_object_or_404(FLRound, round_id=round_id)
    all_updates = fl_round.updates.select_related('device').all().order_by('-uploaded_at')
    
    # Paginate updates: 15 per page
    paginator = Paginator(all_updates, 15)
    page_number = request.GET.get('updates_page', 1)
    updates_page = paginator.get_page(page_number)
    
    context = {
        'round': fl_round,
        'updates': updates_page,
        'total_updates': paginator.count,
        'has_update_pages': updates_page.has_other_pages(),
    }
    return render(request, 'fl/round_detail.html', context)


@login_required
def api_round_updates(request, round_id):
    """API endpoint to fetch model updates for a round dynamically"""
    fl_round = get_object_or_404(FLRound, round_id=round_id)
    
    # Get limit and offset from query params
    limit = min(int(request.GET.get('limit', 15)), 100)
    offset = int(request.GET.get('offset', 0))
    
    # Fetch updates
    all_updates = fl_round.updates.select_related('device').order_by('-uploaded_at')
    updates = all_updates[offset:offset+limit]
    
    # Format response
    updates_data = []
    for u in updates:
        updates_data.append({
            'update_id': str(u.update_id),
            'device_name': u.device.device_name,
            'local_accuracy': float(u.local_accuracy),
            'local_loss': float(u.local_loss),
            'gradient_norm': float(u.gradient_norm),
            'training_samples': u.training_samples,
            'is_malicious': u.is_malicious,
            'uploaded_at': u.uploaded_at.isoformat(),
        })
    
    return JsonResponse({
        'total': all_updates.count(),
        'count': len(updates_data),
        'offset': offset,
        'limit': limit,
        'results': updates_data
    })


@user_passes_test(is_admin)
@user_passes_test(is_admin)
def api_round_status(request, round_id):
    """API endpoint to change FL Round status"""
    fl_round = get_object_or_404(FLRound, round_id=round_id)
    
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=400)
    
    import json
    try:
        data = json.loads(request.body)
        new_status = data.get('status')
    except:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    
    # Validate status
    valid_statuses = ['pending', 'in_progress', 'completed', 'failed']
    if new_status not in valid_statuses:
        return JsonResponse({'error': f'Invalid status. Must be one of: {valid_statuses}'}, status=400)
    
    # Perform transition validation
    current_status = fl_round.status
    
    # Allow transitions
    if current_status == 'pending' and new_status == 'in_progress':
        fl_round.start_round()
        return JsonResponse({'status': 'success', 'message': f'Round {fl_round.round_number} started'})
    
    elif current_status == 'in_progress' and new_status == 'completed':
        # Can complete directly or via aggregate
        updates = list(fl_round.updates.all())
        if updates:
            global_acc = sum(u.local_accuracy for u in updates) / len(updates)
            global_loss = sum(u.local_loss for u in updates) / len(updates)
            fl_round.complete_round(accuracy=global_acc, loss=global_loss)
            return JsonResponse({'status': 'success', 'message': f'Round {fl_round.round_number} completed'})
        else:
            return JsonResponse({'error': 'Cannot complete round without updates'}, status=400)
    
    elif new_status == 'failed':
        fl_round.status = 'failed'
        fl_round.save()
        return JsonResponse({'status': 'success', 'message': f'Round {fl_round.round_number} marked as failed'})
    
    else:
        return JsonResponse(
            {'error': f'Cannot transition from {current_status} to {new_status}'}, 
            status=400
        )


@user_passes_test(is_admin)
def start_new_round(request):
    """Admin: start a new FL round"""
    if request.method == 'POST':
        last_round = FLRound.objects.order_by('-round_number').first()
        next_number = (last_round.round_number + 1) if last_round else 1
        fl_round = FLRound.objects.create(
            round_number=next_number,
            min_participants=settings.FL_SETTINGS['MIN_DEVICES'],
            max_participants=settings.FL_SETTINGS['MAX_DEVICES'],
            status='pending'
        )
        fl_round.start_round()

        # Record on blockchain as a transaction
        tx = CoreTransaction(
            sender="Admin",
            recipient="FLNetwork",
            data={'type': 'START_ROUND', 'round_number': next_number}
        )
        blockchain_instance.add_transaction(tx)

        messages.success(request, f"FL Round {next_number} started.")
        return redirect('federated_learning:round_detail', round_id=fl_round.round_id)

    return render(request, 'fl/start_round.html')


@login_required
def join_round(request, round_id, device_id):
    """User device joins an in-progress round (logical join for simulation)"""
    fl_round = get_object_or_404(FLRound, round_id=round_id)
    device = get_object_or_404(Device, device_id=device_id, user=request.user)

    if fl_round.status != 'in_progress':
        messages.warning(request, 'Round is not open for participation.')
        return redirect('federated_learning:round_detail', round_id=round_id)

    # Ensure privacy budget entry exists
    PrivacyBudget.objects.get_or_create(device=device)

    messages.success(request, f"Device {device.device_name} joined round {fl_round.round_number}.")
    return redirect('federated_learning:round_detail', round_id=round_id)


def _simulate_local_update(fl_round, device, global_weights):
    """
    Simulate local training for a device.
    Here we perturb global weights + random metrics,
    and optionally simulate attacks (SAR/BASR).
    """
    # Start from global weights
    local_weights = {}
    for name, vals in global_weights.items():
        def add_noise(data):
            if isinstance(data, list):
                return [add_noise(item) for item in data]
            else:
                return data + random.uniform(-0.01, 0.01)

        local_weights[name] = add_noise(vals) if isinstance(vals, list) else vals

    # Compute gradient norm approximate (difference from global)
    gradient_norm = calculate_gradient_norm(local_weights)

    # Random local metrics
    local_acc = random.uniform(70, 95)
    local_loss = random.uniform(0.2, 0.8)

    # Attack simulation (some devices become malicious)
    is_malicious = False
    attack_type = None
    attacked_weights = local_weights

    if random.random() < 0.2:  # 20% devices malicious
        if random.random() < 0.5:
            attacked_weights = simulate_sar_attack(local_weights, severity=0.7)
            attack_type = 'SAR'
        else:
            attacked_weights = simulate_basr_attack(local_weights, backdoor_pattern=0.3)
            attack_type = 'BASR'
        is_malicious = True

    return attacked_weights, local_acc, local_loss, gradient_norm, is_malicious, attack_type


@user_passes_test(is_admin)
def simulate_round(request, round_id):
    """
    Admin: simulate complete FL round:
    - For each active device, generate local update (with DP + possible attacks)
    - Store ModelUpdate records
    """
    fl_round = get_object_or_404(FLRound, round_id=round_id)

    if fl_round.status != 'in_progress':
        messages.error(request, 'Round must be in progress to simulate.')
        return redirect('federated_learning:round_detail', round_id=round_id)

    # Initialize FedAvg and global model
    fed = FederatedAveraging()
    global_weights = fed.get_model_weights()

    devices = Device.objects.filter(status='active')[:settings.FL_SETTINGS['MAX_DEVICES']]
    if devices.count() < fl_round.min_participants:
        messages.warning(request, 'Not enough devices to simulate this round.')
        return redirect('federated_learning:round_detail', round_id=round_id)

    local_updates = []
    agg_weights = []
    dp_epsilon = settings.PRIVACY_SETTINGS['EPSILON']
    dp_delta = settings.PRIVACY_SETTINGS['DELTA']
    clip_norm = settings.PRIVACY_SETTINGS['CLIP_NORM']

    for d in devices:
        pb, _ = PrivacyBudget.objects.get_or_create(device=d)
        if pb.remaining_gradient_epsilon <= 0:
            continue

        attacked_weights, acc, loss, grad_norm, is_malicious, attack_type = _simulate_local_update(
            fl_round, d, global_weights
        )

        # Apply DP to gradients/weights
        dp_weights = apply_dp_to_gradients(
            attacked_weights,
            epsilon=min(dp_epsilon, pb.remaining_gradient_epsilon),
            delta=dp_delta,
            clip_norm=clip_norm,
            mechanism='gaussian'
        )
        pb.consume_gradient_budget(0.1)  # consume small budget

        mu = ModelUpdate.objects.create(
            fl_round=fl_round,
            device=d,
            model_weights=json.dumps(dp_weights),
            local_accuracy=acc,
            local_loss=loss,
            training_samples=random.randint(100, 500),
            is_malicious=is_malicious,
            gradient_norm=grad_norm,
            privacy_budget_used=0.1
        )

        local_updates.append(dp_weights)
        agg_weights.append(mu.training_samples)

    if not local_updates:
        messages.error(request, 'No valid device updates for this round.')
        return redirect('federated_learning:round_detail', round_id=round_id)

    fl_round.current_participants = len(local_updates)
    fl_round.save()

    # Attack detection
    run_attack_detection(fl_round)

    messages.success(request, f"Simulated {len(local_updates)} device updates for round {fl_round.round_number}.")
    return redirect('federated_learning:round_detail', round_id=round_id)


@user_passes_test(is_admin)
def aggregate_round(request, round_id):
    """
    Admin: run FedAvg, update global model, update reputations, write to blockchain.
    """
    fl_round = get_object_or_404(FLRound, round_id=round_id)
    updates = list(fl_round.updates.all())
    if not updates:
        messages.error(request, 'No updates to aggregate.')
        return redirect('federated_learning:round_detail', round_id=round_id)

    fed = FederatedAveraging()
    local_weights = [json.loads(u.model_weights) for u in updates]
    sample_counts = [u.training_samples for u in updates]

    aggregated = fed.aggregate_weights(local_weights, aggregation_weights=sample_counts)

    # Evaluate: here we simulate accuracy
    global_acc = sum(u.local_accuracy for u in updates) / len(updates)
    global_loss = sum(u.local_loss for u in updates) / len(updates)

    # Use get_or_create to avoid duplicate key error if aggregate_round is called multiple times
    gm, created = GlobalModel.objects.get_or_create(
        fl_round=fl_round,
        defaults={
            'model_architecture': 'SimpleCNN',
            'model_weights': json.dumps(aggregated),
            'accuracy': global_acc,
            'loss': global_loss,
            'num_parameters': len(aggregated)
        }
    )
    
    # If the model already exists, update it with new aggregated data
    if not created:
        gm.model_weights = json.dumps(aggregated)
        gm.accuracy = global_acc
        gm.loss = global_loss
        gm.num_parameters = len(aggregated)
        gm.save()

    fl_round.complete_round(accuracy=global_acc, loss=global_loss)

    # Update reputation for all devices
    for u in updates:
        rep_engine.update_reputation(u.device, round_number=fl_round.round_number,
                                     reason="Post-FL round aggregation")

    # Record result on blockchain
    tx = CoreTransaction(
        sender="FLNetwork",
        recipient="FLNetwork",
        data={
            'type': 'END_ROUND',
            'round_number': fl_round.round_number,
            'global_acc': global_acc,
            'global_loss': global_loss,
        }
    )
    blockchain_instance.add_transaction(tx)

    # Try to create ledger entry (may fail if block_id constraint is stricter in DB)
    try:
        BlockchainLedger.objects.create(
            fl_round_id=str(fl_round.round_id),
            operation='END_ROUND',
            device_count=fl_round.current_participants,
            global_model_hash=gm.model_id.hex,
            metadata=json.dumps({'acc': global_acc, 'loss': global_loss})
        )
    except Exception as e:
        # Log error but don't block the workflow - transaction is already recorded
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"Failed to create blockchain ledger entry for round {fl_round.round_number}: {e}")

    messages.success(request, f"Round {fl_round.round_number} aggregated. Global acc: {global_acc:.2f}%")
    return redirect('federated_learning:round_detail', round_id=round_id)
