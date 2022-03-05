
$(document).ready(function () {
    $('.timepicker').timepicker({
        timeFormat: 'h:mm p',
        interval: 15,
        minTime: '7:00AM',
        maxTime: '10:00PM',
        dynamic: false,
        dropdown: true,
        scrollbar: true
    });
});

$(document).ready(function () {
    $('#courseTable').DataTable({ "deferRender": true });
    $('#instructorTable').DataTable({ "deferRender": true });
    $('#scheduleTable').DataTable({ "deferRender": true });
    $('#allSchedulesTable').DataTable({ "deferRender": true });
    $('#scheduleDoneTable').DataTable({ "deferRender": true });
    $('#scheduleAddTable').DataTable({ "deferRender": true });
    $('#scheduleDeleteTable').DataTable({ "deferRender": true });
    $('#scheduleChangeTable').DataTable({ "deferRender": true });
});