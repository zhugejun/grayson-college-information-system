# a list of queries will be used in data.py

# Fall 2020, Spring 2021, Fall 2021

TERM_IDS = [534, 546, 548]

SCHEDULE_QUERY = f"select year(TermStartDate) as [year]\
    , case when TextTerm like '%Spr%' then 'Spring'\
           when TextTerm like '%Fal%' then 'Fall' end as semester\
    , Department as subject, CourseID as number, sro.CourseName as name, section\
    , upper(case when g.displaytext='cancelled' then 'canceled' else g.DisplayText end) as [status]\
    , MaximumEnroll as capacity\
    , upper(RTRIM(fac.LastName)) + ', ' + upper(RTRIM(fac.FirstName)) as instructor\
    , case when c.campus in ('', ' ') then null else c.campus end as campus\
    , case when concat(b.Abbreviation, r.Number) in (' ', '') then null\
            when concat(b.Abbreviation, r.Number) = 'NT000' then 'Internet'\
            else concat(b.Abbreviation, r.Number) end as location\
    , case when sch.OfferDays in (' ', '', 'N\\A') then null else sch.OfferDays end as days\
    , cast(sch.OfferTimeFrom as time) as start_time, cast(sch.OfferTimeTo as time) as stop_time\
    join TermCalendar tc on tc.TermCalendarID = sro.TermCalendarID\
    left join campuses c on c.CampusID = sro.CampusID\
    left join SROfferSchedule sch on sro.SROfferID = sch.SROfferID\
    left join Rooms r on sch.OfferRoomID = r.RoomID\
    left join buildings b on b.BuildingID = r.BuildingID\
    left join SROfferSchedule_Faculty schf on sch.SROfferScheduleID = schf.SROfferScheduleID\
    left join Faculty fac on schf.FacultyID = fac.FacultyID\
    left join glossary g on g.uniqueid = sro.statusid\
    where sro.TermCalendarID in ({','.join([str(x) for x in TERM_IDS])})"


TERM_QUERY = f"select year(TermStartDate) as [year]\
    , case when TextTerm like '%Spr%' then 'Spring'\
           when TextTerm like '%Fal%' then 'Fall' end as semester\
    , case when TermStartDate > GETDATE() then 'T' else 'F' end as active\
    from TermCalendar\
    where TermCalendarID in ({','.join([str(x) for x in TERM_IDS])})"


COURSE_QUERY = f"select distinct Department as subject\
    , CourseID as number\
    , Credits as credit\
    , CourseName as [name]\
    from SROffer sro\
    where sro.TermCalendarID in ({','.join([str(x) for x in TERM_IDS])})"


INSTRUCTOR_QUERY = "select distinct EmployeeId, FirstName, LastName\
    , left(g.DisplayText, 1) as HireStatus\
    from Faculty fac\
        join Glossary g on fac.HireStatusID = g.UniqueId\
    where Active = 1 and HireStatusID <> 0"


CAMPUS_QUERY = "select Campus as [name]\
    from Campuses\
    where Campus <> ''\
    order by Campus"


SUBJECT_QUERY = f"select distinct Department as subject\
    from SROffer\
    where TermCalendarID in ({','.join([str(x) for x in TERM_IDS])})\
    order by Department"


LOCATION_QUERY = "select case when b.Abbreviation = 'NT' then 'Inter' else b.Abbreviation end as building\
    , case when b.Abbreviation = 'NT' and r.Number = '000' then 'net' else r.Number end as room\
    from Buildings b\
    join Rooms r on b.BuildingID = r.BuildingID\
    where b.Abbreviation <> '' "
