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


def create_history(instance):
    for field in instance._meta.fields:
        History.objects.create(
            content_object=instance,
            field_name=field.name,
            prev_value=str(None),
            next_value=get_value(instance, field.name),
            action=common_constants.HISTORY_ACTION.CREATE
        )
        logger.debug('Create entry %s for %s' % (instance, field.name))


def update_history(instance):
    changes = instance.tracker.changed()
    print 'xxxxxxxxxxxxxxxxxxxxxxxxxx'
    print changes
    print 'xxxxxxxxxxxxxxxxxxxxxxxxxx'
    for key, value in changes.iteritems():
        kwrgs = {
            'content_object': instance,
            'field_name': key,
            'prev_value': str(value),
            'next_value': get_value(instance, key),
            'action': common_constants.HISTORY_ACTION.UPDATE
        }
        History.objects.create(**kwrgs)
        logger.debug('Update entry %s for %s' % (instance, key))


def delete_history(instance):
    for field in instance._meta.fields:
        History.objects.create(
            content_object=instance,
            field_name=field.name,
            prev_value=get_value(instance, field.name),
            next_value=str(None),
            action=common_constants.HISTORY_ACTION.DELETE
        )
        logger.debug('History entry %s for %s' % (instance, field.name))
