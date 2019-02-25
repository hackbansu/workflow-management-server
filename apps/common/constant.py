from collections import namedtuple

DESIGNATION = namedtuple(
    'DESIGNATION',
    'HR CEO CTO SDE_1 SDE_2'
)._make([1, 2, 3, 4, 5])
USER_STATUS = namedtuple(
    'STATUS',
    'INVITED ACTIVE INACTIVE'
)._make([1, 2, 3])
LINK_TYPE = namedtuple(
    'LINK_TYPE',
    'TWITTER FACEBOOK GOOGLE'
)._make([1, 2, 3])
WORKFLOW_STATUS = namedtuple(
    'WORKFLOW_STATUS',
    'INITIATED SCHEDULED INPROGRESS COMPLETE'
)._make([1, 2, 3, 4])
TASK_STATUS = namedtuple(
    'TASK_STATUS',
    'UPCOMING SCHEDULED ONGOING COMPLETE'
)._make([1, 2, 3, 4])
PERMISSION = namedtuple(
    'PERMISSION',
    'READ READ_WRITE'
)._make([1, 2])
COMPANY_STATUS = namedtuple(
    'COMPANY_STATUS',
    'UNVERIFIED ACTIVE INACTIVE'
)._make([1, 2, 3])
CSV_STATUS = namedtuple(
    'CSV_STATUS',
    'PENDING INPROGRESS PROCESSED ERROR'
)._make([1, 2, 3, 4])

WORKFLOW_START_UPDATE_THRESHOLD_HOURS = 2
TASK_START_UPDATE_THRESHOLD_MINUTES = 15
