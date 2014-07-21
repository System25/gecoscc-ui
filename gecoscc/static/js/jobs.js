/*jslint browser: true, nomen: true, unparam: true */
/*global App */

// Copyright 2014 Junta de Andalucia
//
// Licensed under the EUPL, Version 1.1 or - as soon they
// will be approved by the European Commission - subsequent
// versions of the EUPL (the "Licence");
// You may not use this work except in compliance with the
// Licence.
// You may obtain a copy of the Licence at:
//
// http://ec.europa.eu/idabc/eupl
//
// Unless required by applicable law or agreed to in
// writing, software distributed under the Licence is
// distributed on an "AS IS" basis,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either
// express or implied.
// See the Licence for the specific language governing
// permissions and limitations under the Licence.

App.module("Job", function (Job, App, Backbone, Marionette, $, _) {
    "use strict";

    App.addInitializer(function () {
        // TODO load jobs
    });
});

App.module("Job.Models", function (Models, App, Backbone, Marionette, $, _) {
    "use strict";

    Models.JobModel = Backbone.Model.extend({
        intTwoDigit: function (int) {
            var num = String(int);
            if (num.length === 1) {
                num = "0" + num;
            }
            return num;
        },
        parseDate: function (date) {
            try {
                date = new Date(date);
                var dateFormat = date.getFullYear() + "/" + this.intTwoDigit((date.getMonth() + 1)) + "/" + this.intTwoDigit(date.getDate());
                dateFormat += " " + this.intTwoDigit(date.getHours()) + ":" + this.intTwoDigit(date.getMinutes()) + ":" + this.intTwoDigit(date.getSeconds());
                return dateFormat;
            } catch (err) {
                return date;
            }
        },
        parse: function (obj) {
            obj.created = this.parseDate(obj.created);
            obj.last_update = this.parseDate(obj.last_update);
            return obj;
        },
        url: function () {
            var url = "/api/jobs/";
            if (this.has("id")) {
                url += this.get("id") + '/';
            }
            return url;
        }
    });

    Models.JobCollection = Backbone.Paginator.requestPager.extend({
        model: Models.JobModel,
        paginator_core: {
            type: "GET",
            dataType: "json",
            url: function () {
                // maxdepth must be zero for pagination to work because in the
                // answer from the server there is no information about the
                // number of children in a container (OU)
                return "/api/jobs/";
            }
        },
        paginator_ui: {
            firstPage: 1,
            currentPage: 1,
            perPage: 30,
            pagesInRange: 3,
            // 10 as a default in case your service doesn't return the total
            totalPages: 10
        },
        server_api: {
            page: function () { return this.currentPage; },
            pagesize: function () { return this.perPage; },
            status:  function () {
                return this.status;
            }
        },
        parse: function (response) {
            this.totalPages = response.pages;
            return response.jobs;
        }
    });
    Models.JobStatistics = Backbone.Model.extend({
        url: function () {
            return "/api/jobs-statistics/";
        },
        parse: function (obj) {
            return obj;
        }
    });
});

App.module("Job.Views", function (Views, App, Backbone, Marionette, $, _) {
    "use strict";

    Views.NanoJob = Marionette.ItemView.extend({});

    Views.NanoEvents = Marionette.CompositeView.extend({
        itemView: Views.NanoJob
    });

    Views.Job = Marionette.ItemView.extend({});

    Views.Events = Marionette.CompositeView.extend({
        itemView: Views.Job
    });
});
