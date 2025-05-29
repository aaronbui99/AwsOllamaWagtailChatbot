from django.db import models
from django.contrib.postgres.fields import JSONField  # Django≥3.1 use models.JSONField

class ChatLog(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    messages   = models.JSONField()      # stores your list of dicts
    # optional: session/user foreign key, etc.

    def __str__(self):
        return f"ChatLog #{self.id} at {self.created_at}"
