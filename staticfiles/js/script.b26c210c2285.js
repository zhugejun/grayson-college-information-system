
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


// $(document).ready(function() {
option = {
    animation: true,
    autohide: true,
    delay: 2000
};
var toastElList = [].slice.call(document.querySelectorAll('.toast'));
var toastList = toastElList.map(function (toastEl) {
    return new bootstrap.Toast(toastEl, option);
});
toastElList.forEach(toast => toast.show());
// })
