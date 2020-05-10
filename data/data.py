
import datetime
from .queries import SCHEDULE_QUERY, TERM_QUERY, SUBJECT_QUERY
from .queries import CAMPUS_QUERY, LOCATION_QUERY, COURSE_QUERY, INSTRUCTOR_QUERY
from .helper import get_data_from_cams, get_data_from_db
from .helper import insert_data_into_db, df_to_sql, datetime_to_time, is_table_existing


# no dependent foreignkeys
def load_terms_from_cams(restart=True, tbl_name='scheduling_term'):
    print('[info]Loading term data...')
    terms = get_data_from_cams(TERM_QUERY)
    query = df_to_sql(df=terms,
                      col_names=['year', 'semester', 'active'],
                      col_types=['num', 'str', 'str'],
                      tbl_name=tbl_name,
                      tbl_cols=['year', 'semester', 'active'])
    if restart and not is_table_existing(tbl_name):
        restart = False
    insert_data_into_db(query, restart=restart, tbl_name=tbl_name)


# no dependent foreignkeys
def load_subjects_from_cams(restart=True, tbl_name='main_subject'):
    print('[info]Loading subject data...')
    subjects = get_data_from_cams(SUBJECT_QUERY)
    query = df_to_sql(df=subjects,
                      col_names=['subject'], col_types=['str'],
                      tbl_name=tbl_name, tbl_cols=['subject'])
    if restart and not is_table_existing(tbl_name):
        restart = False
    insert_data_into_db(query, restart=restart, tbl_name=tbl_name)


# no dependent foreignkeys
def load_campuses_from_cams(restart=True, tbl_name='scheduling_campus'):
    print('[info]Loading campus data...')
    campuses = get_data_from_cams(CAMPUS_QUERY)
    query = df_to_sql(df=campuses,
                      col_names=['name'], col_types=['str'],
                      tbl_name=tbl_name, tbl_cols=['name'])
    if restart and not is_table_existing(tbl_name):
        restart = False
    insert_data_into_db(query, restart=restart, tbl_name=tbl_name)


# no dependent foreignkeys
def load_locations_from_cams(restart=True, tbl_name='scheduling_location'):
    print('[info]Loading location data...')
    locations = get_data_from_cams(LOCATION_QUERY)
    query = df_to_sql(df=locations,
                      col_names=['building', 'room'], col_types=['str', 'str'],
                      tbl_name=tbl_name, tbl_cols=['building', 'room'])
    if restart and not is_table_existing(tbl_name):
        restart = False
    insert_data_into_db(query, restart=restart, tbl_name=tbl_name)


# no dependent foreignkeys
def load_instructors_from_cams(restart=True, tbl_name='scheduling_instructor'):
    print('[info]Loading instructor data...')
    instructors = get_data_from_cams(INSTRUCTOR_QUERY)
    query = df_to_sql(df=instructors,
                      col_names=['employeeId', 'first_name',
                                 'last_name', 'hiring_status'],
                      col_types=['str', 'str', 'str', 'str'],
                      tbl_name=tbl_name,
                      tbl_cols=['employeeId', 'first_name',
                                'last_name', 'hiring_status'])
    if restart and not is_table_existing(tbl_name):
        restart = False
    insert_data_into_db(query, restart=restart, tbl_name=tbl_name)


# depends on subject_id
def load_courses_from_cams(restart=True, tbl_name='scheduling_course'):
    print('[info]Loading course data...')
    # at this time, subject table is already loaded
    courses = get_data_from_cams(COURSE_QUERY)
    subjects = get_data_from_db('select * from scheduling_subject')
    courses = courses.merge(subjects, how='inner', on='subject').rename(
        columns={'id': 'subject_id'})[['subject_id', 'number', 'name']]
    query = df_to_sql(df=courses,
                      col_names=['subject_id', 'number', 'name'],
                      col_types=['num', 'str', 'str'],
                      tbl_name=tbl_name,
                      tbl_cols=['subject_id', 'number', 'name'])
    if restart and not is_table_existing(tbl_name):
        restart = False
    insert_data_into_db(query, restart=True, tbl_name=tbl_name)


# schedules depend on ids
def load_schedules_from_cams(restart=True, for_cams=False):

    if not for_cams:
        tbl_name = 'scheduling_schedule'
    else:
        tbl_name = 'scheduling_cams'

    # pulling data from cams
    schedules = get_data_from_cams(SCHEDULE_QUERY)

    # change datetime to datetime.time()
    schedules['start_time'] = schedules['start_time'].apply(datetime_to_time)
    schedules['stop_time'] = schedules['stop_time'].apply(datetime_to_time)

    # term id
    terms = get_data_from_db(
        "select id as term_id, [year], semester from scheduling_term")

    # campus id
    campuses = get_data_from_db(
        "select id as campus_id, campus from scheduling_campus")

    # course id
    courses = get_data_from_db("select sc.id as course_id, ms.subject, sc.number\
        from scheduling_course sc\
        join main_subject ms on sc.subject_id = ms.id")

    # location id
    locations = get_data_from_db(
        "select id as location_id, concat(building, room) as location from scheduling_location")

    # instructor id
    instructors = get_data_from_db("select min(id) as id, concat(upper(last_name), ', ', upper(first_name)) as instructor\
        from scheduling_instructor\
        group by last_name, first_name")

    if not for_cams:
        # insert by id
        schedules['insert_by_id'] = 1
        # update by id
        schedules['update_by_id'] = 1
        # insert_date as today
        schedules['insert_date'] = datetime.datetime.now()
        # update_date as today
        schedules['update_date'] = datetime.datetime.now()
        # note as None
        schedules['notes'] = None

    #------- get ids for columns above --------#
    schedules = schedules.merge(campuses, how='left', on='campus')
    schedules = schedules.merge(courses, how='left', on=['subject', 'number'])
    schedules = schedules.merge(terms, how='left', on=['year', 'semester'])
    schedules = schedules.merge(locations, how='left', on='location')
    schedules = schedules.merge(instructors, how='left', on='instructor')

    schedules['credit'] = schedules['credit'].astype('int')

    schedules_cols = ['term_id', 'course_id', 'section',
                      'credit', 'status', 'capacity', 'instructor_id',
                      'campus_id', 'location_id', 'days', 'start_time',
                      'stop_time', 'insert_date', 'insert_by_id',
                      'update_date', 'update_by_id']
    col_types = ['num', 'num', 'str',
                 'num', 'str', 'num', 'num',
                 'num', 'num', 'str', 'str',
                 'str', 'str', 'num',
                 'str', 'num']

    if for_cams:
        schedules_cols = schedules_cols[:12]
        col_types = col_types[:12]

    schedules = schedules[schedules_cols]

    query = df_to_sql(df=schedules,
                      col_names=schedules_cols,
                      col_types=col_types,
                      tbl_name=tbl_name,
                      tbl_cols=schedules_cols)

    # schedule_script = schedule_script.replace("'None'", "NULL")
    # schedule_script = schedule_script.replace("N\A", "NULL")
    if restart and not is_table_existing(tbl_name):
        restart = False

    insert_data_into_db(query, restart=restart, tbl_name=tbl_name)


# list of steps to do when reseting
def reset_database(restart=True):
    load_terms_from_cams(restart=restart)
    load_subjects_from_cams(restart=restart)
    load_campuses_from_cams(restart=restart)
    load_locations_from_cams(restart=restart)
    load_instructors_from_cams(restart=restart)
    load_courses_from_cams(restart=restart)
    load_schedules_from_cams(restart=restart)


# initialize database for the first time
def initialize_database():
    reset_database(restart=False)


if __name__ == "__main__":
    pass
