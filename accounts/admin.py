from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Device, DeviceMetrics

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['username', 'email', 'user_type', 'is_verified', 'date_joined']
    list_filter = ['user_type', 'is_verified', 'is_active', 'date_joined']
    search_fields = ['username', 'email', 'first_name', 'last_name', 'organization']
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Additional Info', {'fields': ('user_type', 'phone_number', 'organization', 'is_verified')}),
    )


@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
    list_display = ['device_name', 'device_id', 'user', 'device_type', 'status', 'is_malicious', 'created_at']
    list_filter = ['status', 'device_type', 'is_malicious', 'created_at']
    search_fields = ['device_name', 'device_id', 'mac_address', 'ip_address']
    readonly_fields = ['device_id', 'created_at', 'updated_at', 'last_active']
    actions = ['activate_devices', 'block_devices']
    
    def activate_devices(self, request, queryset):
        queryset.update(status='active')
        self.message_user(request, f'{queryset.count()} devices activated.')
    activate_devices.short_description = "Activate selected devices"
    
    def block_devices(self, request, queryset):
        queryset.update(status='blocked', is_malicious=True)
        self.message_user(request, f'{queryset.count()} devices blocked.')
    block_devices.short_description = "Block selected devices"


@admin.register(DeviceMetrics)
class DeviceMetricsAdmin(admin.ModelAdmin):
    list_display = ['device', 'cpu_usage', 'memory_usage', 'network_latency', 'timestamp']
    list_filter = ['timestamp']
    search_fields = ['device__device_name']
    readonly_fields = ['timestamp']
