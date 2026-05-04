from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import JsonResponse
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from django.utils.dateformat import format as date_format
from django.db.models import Count
from django.urls import reverse
from .models import Block as DBBlock, Transaction as DBTransaction, BlockchainLedger
from .blockchain_core import Blockchain, Transaction as CoreTransaction
from accounts.models import Device
from reputation.models import ReputationScore
import json
import hashlib
import uuid
import random

# Single in-memory blockchain instance
blockchain_instance = Blockchain(difficulty=4)


def _create_auto_transaction(device, created_by='system'):
    """Create a default pending transaction so a device can always mine a block."""
    tx_hash = hashlib.sha256(
        f"auto:{device.device_id}:{timezone.now().timestamp()}:{uuid.uuid4()}".encode('utf-8')
    ).hexdigest()
    tx_data = {
        'type': 'AUTO_BLOCK_EVENT',
        'payload': f'Auto-generated transaction for {device.device_name}',
        'created_by': created_by,
    }
    return DBTransaction.objects.create(
        tx_hash=tx_hash,
        sender=str(device.device_id),
        recipient='FLNetwork',
        data=json.dumps(tx_data),
        timestamp=timezone.now(),
        sender_device=device,
        block=None,
    )


def _build_secure_device_block_proof(device_id, block_hash):
    """Create a short secure proof bound to device + block hash."""
    return hashlib.sha256(f"{device_id}:{block_hash}".encode('utf-8')).hexdigest()


def _mine_transactions_for_device(device, device_only=False, created_by='system', auto_create_if_empty=False):
    """Mine pending transactions for one device and persist mined txs in DB."""
    try:
        rep_obj = ReputationScore.objects.filter(device=device).latest('timestamp')
        reputation_score = rep_obj.score
    except ReputationScore.DoesNotExist:
        reputation_score = 0.5
    # Ensure admin-driven mining can proceed consistently for all devices.
    if reputation_score < blockchain_instance.min_reputation:
        reputation_score = blockchain_instance.min_reputation

    if device_only:
        pending_db_txs = DBTransaction.objects.filter(
            block__isnull=True,
            sender_device=device
        ).select_related('sender_device')
    else:
        pending_db_txs = DBTransaction.objects.filter(
            block__isnull=True
        ).select_related('sender_device')

    if not pending_db_txs.exists() and auto_create_if_empty:
        _create_auto_transaction(device, created_by=created_by)
        if device_only:
            pending_db_txs = DBTransaction.objects.filter(
                block__isnull=True,
                sender_device=device
            ).select_related('sender_device')
        else:
            pending_db_txs = DBTransaction.objects.filter(
                block__isnull=True
            ).select_related('sender_device')

    if not pending_db_txs.exists():
        return False, 'No pending transactions available for mining.', 0, None

    blockchain_instance.pending_transactions.clear()
    for db_tx in pending_db_txs:
        try:
            tx_data = json.loads(db_tx.data)
        except (TypeError, json.JSONDecodeError):
            tx_data = {'raw': str(db_tx.data)}

        core_tx = CoreTransaction(
            sender=db_tx.sender,
            recipient=db_tx.recipient,
            data=tx_data,
            timestamp=db_tx.timestamp.timestamp()
        )
        core_tx.tx_hash = db_tx.tx_hash
        blockchain_instance.pending_transactions.append(core_tx)

    new_block = blockchain_instance.mine_pending_transactions(str(device.device_id), reputation_score)
    if not new_block:
        return False, 'No pending transactions or insufficient reputation.', 0, None

    latest_db_block = DBBlock.objects.order_by('-index').first()
    next_index = (latest_db_block.index + 1) if latest_db_block else 1
    previous_hash = latest_db_block.hash if latest_db_block else ('0' * 64)

    db_block = DBBlock.objects.create(
        index=next_index,
        hash=new_block.hash,
        previous_hash=previous_hash,
        timestamp=timezone.now(),
        nonce=new_block.nonce,
        merkle_root=new_block.merkle_root,
        miner_device=device,
        reputation_data=json.dumps(new_block.reputation_scores)
    )

    # Attach existing pending transactions to the new block (no duplicates).
    mined_count = pending_db_txs.count()
    pending_db_txs.update(block=db_block)

    proof = _build_secure_device_block_proof(device.device_id, db_block.hash)
    msg = (
        f'Block {db_block.index} mined for "{device.device_name}" with {mined_count} transaction(s). '
        f'Hash: {db_block.hash[:12]}... | Proof: {proof[:12]}...'
    )
    return True, msg, mined_count, db_block


def is_admin(user):
    return user.is_superuser or getattr(user, 'user_type', '') == 'admin'


def can_mine(user):
    """Allow admin and device-owner users to perform mining operations."""
    return bool(user and user.is_authenticated and (
        user.is_superuser or getattr(user, 'user_type', '') in ('admin', 'device')
    ))


@login_required
def blockchain_overview(request):
    selected_device_id = (request.GET.get('device_id') or '').strip()
    all_devices = Device.objects.all().order_by('device_name')

    blocks_qs = DBBlock.objects.all().select_related('miner_device')
    tx_qs = DBTransaction.objects.all().select_related('sender_device')
    selected_device = None
    if selected_device_id:
        selected_device = Device.objects.filter(device_id=selected_device_id).first()
        if selected_device:
            blocks_qs = blocks_qs.filter(miner_device=selected_device)
            tx_qs = tx_qs.filter(sender_device=selected_device)

    blocks = blocks_qs.order_by('-index')[:20]
    transactions = tx_qs.order_by('-timestamp')[:20]

    block_secure_proofs = {
        str(b.id): _build_secure_device_block_proof(b.miner_device_id, b.hash)
        for b in blocks if b.miner_device_id
    }

    device_block_counts = {
        str(item['miner_device']): item['count']
        for item in DBBlock.objects.filter(miner_device__isnull=False)
        .values('miner_device')
        .annotate(count=Count('id'))
    }
    device_tx_counts = {
        str(item['sender_device']): item['count']
        for item in DBTransaction.objects.filter(sender_device__isnull=False)
        .values('sender_device')
        .annotate(count=Count('id'))
    }

    last_block_by_device = {}
    for device in all_devices:
        latest = DBBlock.objects.filter(miner_device=device).order_by('-index').first()
        if latest:
            last_block_by_device[str(device.device_id)] = latest.hash

    chain_valid = blockchain_instance.is_chain_valid()
    stats = {
        'total_blocks': blocks_qs.count(),
        'total_transactions': tx_qs.count(),
        'pending_transactions': tx_qs.filter(block__isnull=True).count(),
    }
    return render(
        request,
        'blockchain/overview.html',
        {
            'blocks': blocks,
            'transactions': transactions,
            'all_devices': all_devices,
            'can_mine': can_mine(request.user),
            'selected_device': selected_device,
            'selected_device_id': selected_device_id,
            'device_block_counts': device_block_counts,
            'device_tx_counts': device_tx_counts,
            'last_block_by_device': last_block_by_device,
            'block_secure_proofs': block_secure_proofs,
            'chain_valid': chain_valid,
            'stats': stats,
        }
    )


@login_required
def block_list(request):
    selected_device_id = (request.GET.get('device_id') or '').strip()
    devices = Device.objects.all().order_by('device_name')
    blocks_qs = DBBlock.objects.all().select_related('miner_device')
    selected_device = None
    if selected_device_id:
        selected_device = Device.objects.filter(device_id=selected_device_id).first()
        if selected_device:
            blocks_qs = blocks_qs.filter(miner_device=selected_device)
    blocks = blocks_qs.order_by('-index')
    block_secure_proofs = {
        str(b.id): _build_secure_device_block_proof(b.miner_device_id, b.hash)
        for b in blocks if b.miner_device_id
    }
    return render(
        request,
        'blockchain/block_list.html',
        {
            'blocks': blocks,
            'devices': devices,
            'selected_device': selected_device,
            'selected_device_id': selected_device_id,
            'block_secure_proofs': block_secure_proofs,
        }
    )


@login_required
def block_detail(request, block_index):
    block = get_object_or_404(DBBlock, index=block_index)
    transactions = DBTransaction.objects.filter(block=block)
    secure_proof = None
    if block.miner_device_id:
        secure_proof = _build_secure_device_block_proof(block.miner_device_id, block.hash)
    return render(
        request,
        'blockchain/block_detail.html',
        {'block': block, 'transactions': transactions, 'secure_proof': secure_proof}
    )


@login_required
def transaction_list(request):
    selected_device_id = (request.GET.get('device_id') or '').strip()
    devices = Device.objects.all().order_by('device_name')
    tx_qs = DBTransaction.objects.all().select_related('block', 'sender_device')
    selected_device = None
    if selected_device_id:
        selected_device = Device.objects.filter(device_id=selected_device_id).first()
        if selected_device:
            tx_qs = tx_qs.filter(sender_device=selected_device)
    transactions = tx_qs.order_by('-timestamp')
    return render(
        request,
        'blockchain/transaction_list.html',
        {
            'transactions': transactions,
            'devices': devices,
            'selected_device': selected_device,
            'selected_device_id': selected_device_id,
        }
    )


@login_required
def blockchain_stats(request):
    stats = blockchain_instance.get_statistics()
    return render(request, 'blockchain/stats.html', {'stats': stats})


@user_passes_test(can_mine)
@require_http_methods(["GET", "POST"])
def mine_block(request):
    next_url = request.POST.get('next') if request.method == 'POST' else request.GET.get('next')

    if request.method == 'POST':
        miner_device_id = request.POST.get('device_id')
        # Default to strict selected-device mining unless explicitly disabled.
        device_only = request.POST.get('device_only') in ('on', 'true', '1', 'yes', None)
        
        try:
            device = Device.objects.get(device_id=miner_device_id)
        except Device.DoesNotExist:
            messages.error(request, 'Device not found.')
            return redirect(next_url or 'blockchain:mine_block')

        ok, msg, _, _ = _mine_transactions_for_device(
            device,
            device_only=device_only,
            created_by=request.user.username,
            auto_create_if_empty=True
        )
        if ok:
            filter_msg = " (device-only)" if device_only else ""
            messages.success(request, f'{msg}{filter_msg}')
        else:
            messages.warning(request, msg)

        if next_url:
            overview_url = reverse('blockchain:overview')
            # Keep context on selected device so UI immediately shows the new block/tx updates.
            if next_url == overview_url:
                return redirect(f'{overview_url}?device_id={device.device_id}')
            return redirect(next_url)

    devices = Device.objects.all().order_by('device_name')
    pending_transactions = DBTransaction.objects.filter(block__isnull=True).select_related('sender_device').order_by('-timestamp')[:20]
    
    # Count pending transactions per device for UI display
    device_tx_counts = {}
    for device in devices:
        device_tx_counts[str(device.device_id)] = DBTransaction.objects.filter(
            block__isnull=True,
            sender_device=device
        ).count()
    return render(
        request,
        'blockchain/mine.html',
        {
            'devices': devices,
            'pending_transactions': pending_transactions,
            'device_tx_counts': device_tx_counts,
        }
    )


@user_passes_test(can_mine)
@require_http_methods(["POST"])
def mine_all_devices(request):
    """Mine one block per device; creates a tx if device has none pending."""
    next_url = request.POST.get('next') or 'blockchain:overview'
    devices = Device.objects.all().order_by('device_name')

    if not devices.exists():
        messages.warning(request, 'No devices found for mining.')
        return redirect(next_url)

    mined = 0
    skipped = 0
    mined_devices = []
    for device in devices:
        ok, _, _, _ = _mine_transactions_for_device(
            device,
            device_only=True,
            created_by=request.user.username,
            auto_create_if_empty=True
        )
        if ok:
            mined += 1
            mined_devices.append(device.device_name)
        else:
            skipped += 1

    if mined:
        sample = ', '.join(mined_devices[:5])
        more = '' if len(mined_devices) <= 5 else f' and {len(mined_devices) - 5} more'
        messages.success(request, f'Mined {mined} block(s): {sample}{more}.')
    if skipped:
        messages.warning(request, f'Skipped {skipped} device(s) due to mining constraints.')
    return redirect(next_url)


@user_passes_test(can_mine)
@require_http_methods(["POST"])
def mine_random_device(request):
    """Mine a block for one random device based on requirement-driven random selection."""
    next_url = request.POST.get('next') or 'blockchain:overview'
    devices = list(Device.objects.all())
    if not devices:
        messages.warning(request, 'No devices available for random mining.')
        return redirect(next_url)

    device = random.choice(devices)
    ok, msg, _, _ = _mine_transactions_for_device(
        device,
        device_only=True,
        created_by=request.user.username,
        auto_create_if_empty=True
    )
    if ok:
        messages.success(request, f'Random mining complete. {msg}')
    else:
        messages.warning(request, f'Random mining failed for "{device.device_name}". {msg}')
    return redirect(next_url)


@user_passes_test(can_mine)
@require_http_methods(["POST"])
def create_manual_transaction(request):
    """Create a pending transaction manually for a selected device."""
    next_url = request.POST.get('next') or 'blockchain:mine_block'
    device_id = request.POST.get('device_id')
    tx_type = (request.POST.get('tx_type') or 'CUSTOM').strip().upper()
    recipient = (request.POST.get('recipient') or 'FLNetwork').strip() or 'FLNetwork'
    payload = (request.POST.get('payload') or '').strip()

    try:
        device = Device.objects.get(device_id=device_id)
    except Device.DoesNotExist:
        messages.error(request, 'Selected device was not found.')
        return redirect(next_url)

    tx_hash = hashlib.sha256(
        f"manual:{device.device_id}:{tx_type}:{timezone.now().timestamp()}:{uuid.uuid4()}".encode('utf-8')
    ).hexdigest()

    tx_data = {
        'type': tx_type,
        'payload': payload,
        'created_by': request.user.username,
    }

    DBTransaction.objects.create(
        tx_hash=tx_hash,
        sender=str(device.device_id),
        recipient=recipient,
        data=json.dumps(tx_data),
        timestamp=timezone.now(),
        sender_device=device,
        block=None,
    )

    messages.success(request, f'Transaction created for device "{device.device_name}" and queued for mining.')
    return redirect(next_url)


@user_passes_test(is_admin)
def verify_chain(request):
    is_valid = blockchain_instance.is_chain_valid()
    return JsonResponse({'valid': is_valid})


@login_required
def recent_transactions_api(request):
    """Return recent transactions for live UI refresh."""
    selected_device_id = (request.GET.get('device_id') or '').strip()
    txs = DBTransaction.objects.all().select_related('sender_device').order_by('-timestamp')
    if selected_device_id:
        selected_device = Device.objects.filter(device_id=selected_device_id).first()
        if selected_device:
            txs = txs.filter(sender_device=selected_device)
    txs = txs[:30]
    data = []
    for tx in txs:
        try:
            tx_data = json.loads(tx.data) if tx.data else {}
        except (TypeError, json.JSONDecodeError):
            tx_data = {}
        data.append({
            'tx_hash_short': f"{tx.tx_hash[:12]}...",
            'sender_device': tx.sender_device.device_name if tx.sender_device else 'SYSTEM',
            'tx_type': tx_data.get('type', 'N/A'),
            'status': 'Confirmed' if tx.block_id else 'Pending',
            'status_class': 'success' if tx.block_id else 'warning',
            'timestamp': date_format(timezone.localtime(tx.timestamp), 'Y-m-d H:i:s'),
        })
    return JsonResponse({'transactions': data})
