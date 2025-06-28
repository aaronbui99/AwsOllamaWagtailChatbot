from django.contrib import admin
from django.utils.html import format_html
from .models import ChatLog

@admin.register(ChatLog)
class ChatLogAdmin(admin.ModelAdmin):
    list_display = ('id', 'created_at', 'truncated_prompt', 'truncated_response', 'model_name', 'user')
    list_filter = ('created_at', 'model_name', 'user')
    search_fields = ('user_prompt', 'ai_response', 'user__username')
    readonly_fields = ('created_at', 'updated_at', 'messages_formatted', 'user_prompt', 'ai_response')
    date_hierarchy = 'created_at'
    
    def truncated_prompt(self, obj):
        if obj.user_prompt:
            return obj.user_prompt[:50] + '...' if len(obj.user_prompt) > 50 else obj.user_prompt
        return "-"
    truncated_prompt.short_description = "User Prompt"
    
    def truncated_response(self, obj):
        if obj.ai_response:
            return obj.ai_response[:50] + '...' if len(obj.ai_response) > 50 else obj.ai_response
        return "-"
    truncated_response.short_description = "AI Response"
    
    def messages_formatted(self, obj):
        if not obj.messages:
            return "-"
        
        html = '<div style="max-width: 800px;">'
        for msg in obj.messages:
            role = msg.get('role', '')
            content = msg.get('content', '')
            
            if role == 'system':
                html += f'<div style="background-color: #f0f0f0; padding: 10px; margin-bottom: 10px; border-radius: 5px;">'
                html += f'<strong>System:</strong><br/>{content}'
                html += '</div>'
            elif role == 'user':
                html += f'<div style="background-color: #e6f7ff; padding: 10px; margin-bottom: 10px; border-radius: 5px;">'
                html += f'<strong>User:</strong><br/>{content}'
                html += '</div>'
            elif role == 'assistant':
                html += f'<div style="background-color: #f6ffed; padding: 10px; margin-bottom: 10px; border-radius: 5px;">'
                html += f'<strong>Assistant:</strong><br/>{content}'
                html += '</div>'
            else:
                html += f'<div style="padding: 10px; margin-bottom: 10px; border: 1px solid #ccc; border-radius: 5px;">'
                html += f'<strong>{role}:</strong><br/>{content}'
                html += '</div>'
        
        html += '</div>'
        return format_html(html)
    messages_formatted.short_description = "Conversation"
