# Device Metrics System - ShieldDFL

## Overview
The Recent Metrics system tracks real-time performance metrics for all IoT devices, including CPU usage, memory usage, network latency, battery level, uptime, and data size.

## Features Implemented

### 1. Auto-Generation for New Devices
When a new device is registered, it automatically receives 5 baseline metrics spanning the last 5 minutes.

**How it works:**
- `initialize_device_records()` in `accounts/views.py` creates metrics during device registration
- New metrics have randomized but realistic values:
  - CPU: 20-60%
  - Memory: 30-70%
  - Network latency: 10-50ms
  - Battery: 70-100%

### 2. Live Auto-Refresh
Device detail page (`/accounts/devices/{device_id}/`) auto-refreshes metrics every 5 seconds.

**Implementation:**
- API endpoint: `/accounts/devices/{device_id}/metrics/`
- Returns JSON with latest 20 metrics
- JavaScript `fetch()` polls every 5s and updates table dynamically

### 3. Continuous Metrics Collection
Simulates ongoing data collection from devices.

**Management Command:**
```bash
# Generate 1 new metric for each device
python manage.py collect_device_metrics

# Keep only last 50 metrics per device (default: 100)
python manage.py collect_device_metrics --keep 50
```

**Usage:**
- Run periodically (e.g., every 5 minutes via cron/scheduler)
- Automatically cleans up old metrics to prevent database bloat
- Each device gets 1 new metric per run

### 4. Bulk Metrics Generation
For testing or populating historical data.

**Management Command:**
```bash
# Generate 20 metrics per device
python manage.py generate_metrics --count 20

# Clear all existing metrics first
python manage.py generate_metrics --count 50 --clear
```

## API Endpoints

### Get Device Metrics (JSON)
**Endpoint:** `GET /accounts/devices/{device_id}/metrics/`

**Response:**
```json
{
  "metrics": [
    {
      "timestamp": "2026-03-09 18:07:00",
      "cpu_usage": 70.67,
      "memory_usage": 29.11,
      "network_latency": 75.54,
      "battery_level": 83.53,
      "uptime": 18000,
      "data_size": 8500000
    },
    ...
  ]
}
```

## Database Schema

**Model:** `DeviceMetrics` (accounts/models.py)

| Field | Type | Description |
|-------|------|-------------|
| device | FK(Device) | Associated device |
| cpu_usage | Float | CPU usage percentage (0-100) |
| memory_usage | Float | Memory usage percentage (0-100) |
| network_latency | Float | Network round-trip time (ms) |
| battery_level | Float | Battery percentage (0-100) |
| data_size | BigInt | Data transferred (bytes) |
| uptime | Integer | Device uptime (seconds) |
| timestamp | DateTime | Metric collection time |

## Automation Recommendations

### Linux/Mac (crontab)
```bash
# Collect metrics every 5 minutes
*/5 * * * * cd /path/to/ShieldDFL && /path/to/python manage.py collect_device_metrics --keep 100 >> /var/log/shielddfl_metrics.log 2>&1
```

### Windows (Task Scheduler)
1. Open Task Scheduler
2. Create Basic Task: "ShieldDFL Metrics Collection"
3. Trigger: Daily, repeat every 5 minutes
4. Action: Start Program
   - Program: `python.exe`
   - Arguments: `manage.py collect_device_metrics --keep 100`
   - Start in: `D:\ShieldDFL1111111\ShieldDFL`

### Django Background Task (Celery)
```python
# tasks.py
from celery import shared_task
from django.core.management import call_command

@shared_task
def collect_device_metrics():
    call_command('collect_device_metrics', keep=100)
```

## Testing

### Test New Device Metrics
```bash
python scripts/test_new_device_metrics.py
```
Creates a new device and verifies 5 metrics are auto-generated.

### Test API Endpoint
```bash
python scripts/test_metrics.py
```
Shows sample metrics and JSON API response.

## Maintenance

### Check Metrics Count
```bash
python manage.py shell -c "from accounts.models import DeviceMetrics; print(f'Total metrics: {DeviceMetrics.objects.count()}')"
```

### Delete Old Metrics (older than 30 days)
```python
from datetime import timedelta
from django.utils import timezone
from accounts.models import DeviceMetrics

cutoff = timezone.now() - timedelta(days=30)
old_count = DeviceMetrics.objects.filter(timestamp__lt=cutoff).count()
DeviceMetrics.objects.filter(timestamp__lt=cutoff).delete()
print(f"Deleted {old_count} old metrics")
```

## Troubleshooting

**Issue:** No metrics showing on device detail page
- **Solution:** Run `python manage.py generate_metrics --count 10`

**Issue:** Metrics not updating dynamically
- **Solution:** Check browser console for JavaScript errors, verify API endpoint returns valid JSON

**Issue:** Too many metrics slowing down queries
- **Solution:** Run `python manage.py collect_device_metrics --keep 50` to limit to 50 metrics per device
