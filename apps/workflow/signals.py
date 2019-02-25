from apps.common import constant as common_constant


def send_mail_on_workflow_update(sender, instance, created, **kwargs):
    '''
    sends mail on task update.
    '''
    if not created:
        instance.send_mail(associated_people_details=None, is_updated=True)


def send_mail_on_task_update(sender, instance, created, **kwargs):
    '''
    sends mail on task update.
    '''
    if not created:
        if instance.status == common_constant.TASK_STATUS.COMPLETE:
            instance.send_mail(is_completed=True)
        elif 'status' in kwargs['update_fields']:
            instance.send_mail(is_started=True)
        else:
            instance.send_mail()
