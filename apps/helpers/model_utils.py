import reversion 

from django.utils.timezone import localtime
from django.db import models

class ReversionModel(models.Model):
    class Meta:
        abstract = True

    deleted_on = models.DateTimeField(auto_now_add=False, auto_now=False, null=True, blank=True)

    def soft_delete(self, *args, **kwargs): 
        self.deleted_on = localtime()
        self.save(*args, **kwargs)

    def save(self, *args, **kwargs): 
        with reversion.create_revision():
            super(ReversionModel, self).save(*args, **kwargs)