/* jslint browser: true, devel: true */

(function ($) {

    "use strict";

    $.fn.userlog = function (options) {
        var ws = new WebSocket(options.wsuri),
            big_brother = options.big_brother,
            token = options.token,
            table = $(this),
            thead = table.find('thead'),
            tbody = table.find('tbody'),
            connected = false,
            row = 1;

        ws.onopen = function () {
            connected = true;

            ws.send(token);

            $('<tr>')
                .append(
                    big_brother ? '<th>' + gettext('User') + '</th>' : '',
                    '<th>' + gettext('Time') + '</th>',
                    '<th>' + gettext('URL') + '</th>',
                    '<th>' + gettext('Type') + '</th>',
                    '<th>' + gettext('Result') + '</th>'
                )
                .appendTo(thead);
        };

        ws.onmessage = function (event) {
            var line = JSON.parse(event.data),
                time,
                url,
                type,
                result;

            time = new Date(line.time * 1000);
            try {
                // Time zone don't work well in JavaScript, don't bother.
                time = time.toLocaleString(options.locale);
            } catch (ignore) {
                // The default formatting will be used, it's good enough.
            }

            if (line.method === 'GET') {
                url = '<a href="' + line.path + '">' + line.path + '</a>';
            } else {
                url = line.path;
            }

            if (line.method === 'GET') {
                type = gettext('Read');
            } else if (line.method === 'POST') {
                type = gettext('Write');
            } else {
                type = gettext('Other');
            }
            type += ' (' + line.method + ')';

            result = line.code;

            if (line.code < 200) {
                result = gettext('Informational');
            } else if (line.code < 300) {
                result = gettext('Success');
            } else if (line.code < 400) {
                result = gettext('Redirection');
            } else if (line.code < 500) {
                result = gettext('Client error');
            } else if (line.code < 600) {
                result = gettext('Server error');
            } else {
                result = gettext('Non-standard');
            }
            result += ' (' + line.code + ')';

            row = 3 - row;      // 1 <-> 2
            $('<tr>')
                .addClass('row' + row)
                .hide()
                .append(
                    big_brother ? '<td>' + line.username + '</td>' : '',
                    '<td>' + time + '</td>',
                    '<td>' + url + '</td>',
                    '<td>' + type + '</td>',
                    '<td style="background-color: #' + (line.code < 400 ? 'DDFFDD' : 'FFEFEF') + ';">' + result + '</td>'
                )
                .prependTo(tbody)
                .fadeIn();
        };

        ws.onclose = function () {
            if (connected) {
                // This will also happen when navigating away from the page.
                table.css({opacity: 0.5});
            } else {
                alert("Failed to connect. Is the realtime endpoint running?");
            }
        };
    };

}(django.jQuery));
