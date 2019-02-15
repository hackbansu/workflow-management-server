from celery import shared_task

from apps.common import constant as common_constant
from apps.company.serializers import InviteEmployeeCsvSerializer
from apps.common.helper import parse_invite_csv
from apps.company.models import UserCompany, UserCompanyCsv

@shared_task
def invite_via_csv(csv_object_id):
    csv_instance = UserCompanyCsv.objects.get(pk=csv_object_id)

    # update the status of the csv file to in-progress
    csv_instance.status = common_constant.CSV_STATUS.INPROGRESS
    csv_instance.save()
    print("status updated to in progress")

    data = parse_invite_csv(csv_instance.csv_file)

    if data is None:
        # update the status of the csv file to error
        csv_instance.status = common_constant.CSV_STATUS.ERROR
        csv_instance.save()
        print("status updated to error 1")
        return

    serializer = InviteEmployeeCsvSerializer(data=data, context={'request': {
        'user': csv_instance.user_company.user
    }}, many=True)
    is_valid = serializer.is_valid(raise_exception=False)

    if not is_valid:
        # update the status of the csv file to error
        csv_instance.status = common_constant.CSV_STATUS.ERROR
        csv_instance.save()
        print("status updated to error 2")
        return

    serializer.save()

    # update the status of the csv file to processed
    csv_instance.status = common_constant.CSV_STATUS.PROCESSED
    csv_instance.save()
    print("status updated to processed")
