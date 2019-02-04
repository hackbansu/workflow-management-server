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
TASK_STATUS = namedtuple(
    'TASK_STATUS',
    'UPCOMMING ONGOING COMPLETE'
)._make([1, 2, 3])
PERMISSION = namedtuple(
    'PERMISSION',
    'READ READ_WRITE'
)._make([1, 2])
COMPANY_STATUS = namedtuple(
    'COMPANY_STATUS',
    'UNVERIFIED ACTIVE INACTIVE'
)._make([1, 2, 3])

SYSTEM_EMAIL = 'workflow.platform@jtg'

RESET_PASSWORD_EMAIL = {
    'subject': '[do not reply] Password Reset Request',
    'from_email': SYSTEM_EMAIL
}

NEW_COMPANY_EMAIL = {
    'subject': '[do not reply] New Company Request',
    'from_email': SYSTEM_EMAIL
}
