import reversion 

class ReversionModel():
    def save(self, *args, **kwargs): 
        with reversion.create_revision():
            super(ReversionModel, self).save(*args, **kwargs)