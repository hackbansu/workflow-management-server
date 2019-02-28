from datetime import timedelta

from apps.common import constant as common_constant


def get_parent_start_time(task_parent):
    '''
    Calculates the exact date and time after completion of the parent task till current task.

    Arguments:
        task_parent {Task} -- Task model instance

    Returns:
        datetime -- exact date and time after completion of the parent task till current task.
    '''

    initial_task = task_parent
    task_start_time = timedelta(0)
    while task_parent and not task_parent.completed_at:
        task_start_time += task_parent.start_delta + task_parent.duration
        task_parent = task_parent.parent_task
    if task_parent:
        return task_parent.completed_at + task_start_time
    else:
        return initial_task.workflow.start_at + task_start_time


def is_time_conflicting(t1_start_time, t1_end_time, t2_start_time, t2_end_time):
    '''
    Checks if the two task times conflict

    Arguments:
        t1_start_time {datetime} -- start time of the first task.
        t1_end_time {datetime} -- end time of the first task.
        t2_start_time {datetime} -- start time of the second task.
        t2_end_time {datetime} -- end time of the second task.

    Returns:
        boolean -- Whether timings conflict or not.
    '''

    if ((t2_start_time <= t1_start_time and t2_end_time <= t1_start_time) or
            (t2_start_time >= t1_end_time and t2_end_time >= t1_end_time)):
        return False

    return True


def is_task_conflicting(employee, task_start_time, task_end_time, visited=None, ignore_tasks_ids=[]):
    '''
    Checks whether the tasks of the employee conflict with the new task timings.

    Arguments:
        employee {UserCompany} -- UserCompany model instance
        task_start_time {datetime} -- start time of the new task
        task_end_time {datetime} -- end time of the new task

    Keyword Arguments:
        visited {boolean} -- dictionary containing the pre-computed values of the employee's other
                                tasks timings (default: {None})
        ignore_tasks_ids {list} -- tasks to ignore (could contain the task's id who's timings are
                                     updated) (default: {[]})

    Returns:
        boolean -- Whether new timings conflict with other tasks of the employee
    '''

    if(visited and visited[employee.id]):
        other_tasks = visited[employee.id]
        for other_task in other_tasks:
            expected_start_time, expected_end_time = other_task
            if is_time_conflicting(task_start_time, task_end_time, expected_start_time, expected_end_time):
                return True

        return False

    if(visited):
        visited[employee.id] = []
    filtered_tasks = employee.tasks.exclude(id__in=ignore_tasks_ids)
    other_tasks = filtered_tasks.filter(status__in=[common_constant.TASK_STATUS.UPCOMING,
                                                    common_constant.TASK_STATUS.ONGOING])
    # calculate expected start and end times of other tasks and check conflict
    for other_task in other_tasks.all():
        expected_start_time = other_task.start_delta
        other_task_parent = other_task.parent_task
        if(other_task_parent):
            expected_start_time += get_parent_start_time(other_task_parent)
        else:
            expected_start_time += other_task.workflow.start_at
        expected_end_time = expected_start_time + other_task.duration
        # check for conflict
        if is_time_conflicting(task_start_time, task_end_time, expected_start_time, expected_end_time):
            return True

        # save the calculations
        if(visited):
            visited[employee.id].append((expected_start_time, expected_end_time))

    return False
