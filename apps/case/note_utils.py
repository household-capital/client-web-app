
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from django_comments.models import Comment


def add_case_note(case, content, user=None):
    user_name = user.profile.username if user else 'Unknown',
    user_email = user.email if user else '',

    note = Comment(
        content_type=ContentType.objects.get_for_model(case),
        object_pk=case.caseID,
        user_name=user_name,
        user=user,
        user_email=user_email,
        user_url='',
        comment=content,
        submit_date=timezone.now(),
        site_id=1,
        is_public=True,
        is_removed=False
    )
    note.save()
