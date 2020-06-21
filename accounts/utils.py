from common.models import TaskLog


def import_in_process_for_user(user_id):
    return TaskLog.objects.filter(
        name='import_papers_for_user',
        args=str((user_id,)),
        status=TaskLog.RUNNING
    ).exists()
