/*jslint browser: true, nomen: true, unparam: true, vars: false */
/*global io, jQuery */

/*
* Copyright 2013, Junta de Andalucia
* http://www.juntadeandalucia.es/
*
* Authors:
*   Pablo Martin <goinnn@gmail.com>
*   Emilio Sanchez <emilio.sanchez@gmail.com>
*
* All rights reserved - EUPL License V 1.1
* https://joinup.ec.europa.eu/software/page/eupl/licence-eupl
*/
var socket_io_silent_disconnect = false;

var MessageManager = function () {
    "use strict";
    var manager_handlers = {};

    // Handled by TailNamespace
    var tail = io.connect("/tail");
    //var tail = io.connect("http://localhost/tail", {'force new connection': true});

    // "sendlog" event will fire on "tail" socket
    tail.emit('sendlog');

    tail.on('connect', function (result) {
        startLogging();
    });

    tail.on('logdata', function (result) {
        var handlers,
            handler,
            i;

        if (result.hasOwnProperty('redis')) {
            if (result.redis === 'error') {
                $("#redis-modal").modal({backdrop: 'static'});
            }
        }
        if (result.hasOwnProperty('action')) {
            handlers = manager_handlers[result.action] || [];
            for (i = 0; i < handlers.length; i += 1) {
                handler = handlers[i];
                handler(result);
            }
        }
    });

    tail.on('disconnect', function (reason) {
        if (socket_io_silent_disconnect)
            return;

        if (typeof reason !== "undefined") {
            $("#socket-modal-reason").innerHTML = '('+reason+')';
        }
        else {
            $("#socket-modal-reason").innerHTML = '';
        }
        $("#socket-modal").modal({backdrop: 'static'});
    });


    return {
        bind: function (action, callback) {
            var handlers = manager_handlers[action] = manager_handlers[action] || [];
            handlers.push(callback);
            return this;
        },
        silent_disconnect: function() {
            socket_io_silent_disconnect = true;
        },
        socket: tail
    };
};