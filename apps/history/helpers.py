import logging

from apps.history.models import History
from apps.common import constant as common_constants

# This should be fired before saving data into the modal.

logger = logging.getLogger(__name__)


def get_value(instance, field):
    if instance._meta.get_field(field).get_internal_type() == 'ForeignKey':
        next_value = str(
            getattr(
                instance,
                '{field_name}_id'.format(field_name=field)
            )
        )
    else:
        next_value = str(getattr(instance, field))
    return next_value


def get_history(content_object, field_name, prev_value, next_value, action):
    return History(
        content_object=content_object,
        field_name=field_name,
        prev_value=prev_value,
        next_value=next_value,
        action=action
    )


def create_history(instance):
    histories = [
        get_history(
            instance,
            field.name,
            str(None),
            get_value(instance, field.name),
            common_constants.HISTORY_ACTION.CREATE
        ) for field in instance._meta.fields
    ]
    logger.debug('Create History entry of %s ' % instance)
    History.objects.bulk_create(histories)


def update_history(instance):
    changes = instance.tracker.changed()
    histories = [
        get_history(
            instance,
            key,
            str(value),
            get_value(instance, key),
            common_constants.HISTORY_ACTION.UPDATE
        ) for key, value in changes.iteritems()
    ]
    logger.debug('Update History entry of %s' % (instance))
    History.objects.bulk_create(histories)


def delete_history(instance):
    histories = [
        get_history(
            instance,
            field.name,
            get_value(instance, field.name),
            str(None),
            common_constants.HISTORY_ACTION.DELETE
        ) for field in instance._meta.fields
    ]
    logger.debug('Delete History entry of %s' % (instance, field.name))


def create_bulk_history(instances):
    histories = [
        get_history(
            instance,
            field.name,
            str(None),
            get_value(instance, field.name),
            common_constants.HISTORY_ACTION.CREATE
        )
        for instance in instances for field in instance._meta.fields
    ]
    logger.debug('Create Bulk History entry')
    History.objects.bulk_create(histories)


def update_bulk_history(instances):
    histories = [
        get_history(
            instance,
            key,
            str(value),
            get_value(instance, key),
            common_constants.HISTORY_ACTION.UPDATE
        ) for instance in instances for key, value in instance.tracker.changed().iteritems()
    ]
    logger.debug('Update Bulk History entry')
    History.objects.bulk_create(histories)


def delete_bulk_history(instances):
    histories = [
        get_history(
            instance,
            field.name,
            get_value(instance, field.name),
            str(None),
            common_constants.HISTORY_ACTION.DELETE
        ) for instance in instances for field in instance._meta.fields
    ]
    logger.debug('Delete Bulk History entry')
    History.objects.bulk_create(histories)
