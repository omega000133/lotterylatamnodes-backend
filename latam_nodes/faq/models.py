from django.db import models
from latam_nodes.base.models import BaseModel

class Faq(BaseModel):
    title = models.CharField(max_length=255)
    content = models.TextField()
    priority = models.IntegerField(default=0)
    
    def __str__(self) -> str:
        return self.title