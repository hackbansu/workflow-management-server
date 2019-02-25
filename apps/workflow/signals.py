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
        instance.send_mail()
