
from config.celery import app
from django.dispatch import receiver
from django_comments.signals import comment_was_posted
from django_comments.signals import comment_was_flagged


def is_enquiry_note(comment):
    content_type = comment.content_type
    return content_type.app_label == 'enquiry' and content_type.model == 'enquiry'


@receiver(comment_was_posted)
def handle_post_comment(sender, **kwargs):
    comment = kwargs['comment']
    if is_enquiry_note(comment):
        app.send_task('SF_Create_Enquiry_Note', kwargs={'note_id': str(comment.id)})


@receiver(comment_was_flagged)
def handle_flag_comment(sender, **kwargs):
    comment = kwargs['comment']
    if comment.is_removed and is_enquiry_note(comment):
        app.send_task('SF_Delete_Enquiry_Note', kwargs={'note_id': str(comment.id)})
