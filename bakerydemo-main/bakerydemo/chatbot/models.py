from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone

class ChatLog(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    messages = models.JSONField()  # stores the full conversation as a list of dicts
    
    # Extract and store the user prompt and AI response separately for easier querying
    user_prompt = models.TextField(blank=True)
    ai_response = models.TextField(blank=True)
    
    # Optional: link to a user if they're authenticated
    user = models.ForeignKey(
        get_user_model(),
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='chat_logs'
    )
    
    # Optional: session key for anonymous users
    session_key = models.CharField(max_length=40, blank=True, null=True)
    
    # Model name used for the response
    model_name = models.CharField(max_length=100, default="deepseek-bakery-expert")
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Chat Log"
        verbose_name_plural = "Chat Logs"
    
    def __str__(self):
        return f"ChatLog #{self.id} at {self.created_at.strftime('%Y-%m-%d %H:%M')}"
    
    def save(self, *args, **kwargs):
        # Extract user prompt and AI response from messages if available
        if self.messages and isinstance(self.messages, list):
            for msg in self.messages:
                if msg.get('role') == 'user':
                    self.user_prompt = msg.get('content', '')
                elif msg.get('role') == 'assistant':
                    self.ai_response = msg.get('content', '')
        
        super().save(*args, **kwargs)
