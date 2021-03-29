
from config.celery import app
from django.dispatch import receiver
from django_comments.signals import comment_was_posted
from django_comments.signals import comment_was_flagged


def is_case_note(comment):
    content_type = comment.content_type
    return content_type.app_label == 'case' and content_type.model == 'case'


@receiver(comment_was_posted)
def handle_post_comment(sender, **kwargs):
    print('Case handle_post_comment')
    comment = kwargs['comment']
    if is_case_note(comment):
        app.send_task('SF_Create_Case_Note', kwargs={'note_id': str(comment.id)})


@receiver(comment_was_flagged)
def handle_flag_comment(sender, **kwargs):
    print('Case handle_flag_comment')
    comment = kwargs['comment']
    if comment.is_removed and is_case_note(comment):
        app.send_task('SF_Delete_Case_Note', kwargs={'note_id': str(comment.id)})

