from django.db import models
from accounts.models import Login


class ChatMessage(models.Model):
    user = models.ForeignKey(Login, on_delete=models.CASCADE)
    message = models.TextField()
    response = models.TextField()
    session_id = models.CharField(max_length=100, default='default')
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'chatbot_chat_message'
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.user.username}: {self.message[:30]}"
