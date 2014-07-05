/* jslint browser: true, devel: true */

(function ($) {

    "use strict";

    $.fn.userlog = function (options) {
        var ws = new WebSocket(options.wsuri),
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
                    '<th>Time</th>',
                    '<th>URL</th>',
                    '<th>Type</th>',
                    '<th>Result</th>'
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
                type = 'Read';
            } else if (line.method === 'POST') {
                type = 'Write';
            } else {
                type = 'Other';
            }
            type += ' (' + line.method + ')';

            result = line.code;

            if (line.code < 200) {
                result = 'Informational';
            } else if (line.code < 300) {
                result = 'Success';
            } else if (line.code < 400) {
                result = 'Redirection';
            } else if (line.code < 500) {
                result = 'Client error';
            } else if (line.code < 600) {
                result = 'Server error';
            } else {
                result = 'Non-standard';
            }
            result += ' (' + line.code + ')';

            row = 3 - row;      // 1 <-> 2
            $('<tr>')
                .addClass('row' + row)
                .hide()
                .append(
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

}(jQuery));
