function prepData(data) {
    return data.map(item => {
        return [Date.parse(item[0]), parseFloat(item[1])]
    })
};

function getBoolean(value) {
    switch (value) {
        case true:
        case "true":
        case 1:
        case "1":
        case "on":
        case "yes":
            return true;
        default:
            return false;
    }
}

const arrAvg = arr => arr.reduce((a, b) => a + b[1], 0) / arr.length;
const arrMin = arr => arr.reduce((min, p) => p[1] < min ? p[1] : min, 0);
const arrMax = arr => arr.reduce((min, p) => p[1] > min ? p[1] : min, 0);

function bytes(bytes, label) {
    if (bytes == 0) return '0';
    let s = ['b', 'KB', 'MB', 'GB', 'TB', 'PB'];
    let e = Math.floor(Math.log(bytes) / Math.log(1024));
    let value = ((bytes / Math.pow(1024, Math.floor(e))).toFixed(2));
    e = (e < 0) ? (-e) : e;
    if (label) value += ' ' + s[e];
    return value;
}

function requestData(e) {
    let chart = e.target;
    let $elem = $(chart.renderTo);

    function __get_chart_data(key) {
        return $elem.data(key);
    }

    function set_chart_data(key, value) {
        $elem.data(key, value);
    }

    $.ajax({
        url: __get_chart_data('url'),
        data: {
            'fromMin': __get_chart_data('fromMin'),
            'fromHours': __get_chart_data('fromHours'),
            'fromDays': __get_chart_data('fromDays'),
            'fromWeek': __get_chart_data('fromWeek'),
            'toMin': __get_chart_data('toMin'),
            'toHours': __get_chart_data('toHours'),
            'toDays': __get_chart_data('toDays'),
            'from': __get_chart_data('from'),
            'to': __get_chart_data('to'),
        },

        error: function () {
            set_chart_data('timeOutHdlr', setTimeout(function () {
                requestData({target: chart});
            }, 60000));
        },
        success: function (data) {
            let min = [];
            let avg = [];
            let max = [];
            let labelPrefix = __get_chart_data('labelPrefix')
            let moreThenOne = Object.keys(data).length > 1;
            let formatName = (key) => {
                return labelPrefix + (moreThenOne ? key : '')
            }

            let visibleSeries = [];
            if (chart.series) {
                if (chart.series.length == 0) {
                    Object.keys(data).forEach(item => visibleSeries.push(formatName(item)));
                    let hiddenOnStart = __get_chart_data('hiddenOnStart');
                    if (hiddenOnStart) {
                        hiddenOnStart = hiddenOnStart.split(',');
                        visibleSeries = visibleSeries.filter(item => !hiddenOnStart.includes(item));
                    }
                }
                chart.series.forEach(item => {
                    if (item.visible) {
                        visibleSeries.push(item.name);
                    }
                    item.remove(true);
                });
                chart.legend.allItems.forEach(item => {
                    if (item.visible) {
                        visibleSeries.push(item.name);
                    }
                    item.remove(true)
                });
                chart.redraw();
            }

            let calcMinMax = __get_chart_data('calcMinMax')
            for (let key in data) {
                let values = prepData(data[key]);
                if (values && values.length > 0) {
                    let tmpDate = new Date(values[0][0]);
                    set_chart_data('timezoneOffset', (-1) * tmpDate.getTimezoneOffset() * 60000);
                }
                let series = chart.series[key];
                if (!series) {
                    let name = formatName(key);
                    chart.addSeries({
                            name: name,
                            connectNulls: false,
                            data: values,
                            visible: visibleSeries.includes(name)
                        },
                        false
                    );
                } else {
                    series.setData(values);
                }
                if (calcMinMax) {
                    min.push(arrMin(values));
                    max.push(arrMax(values));
                    avg.push(arrAvg(values).toFixed(2));
                }

            }

            if (calcMinMax) {
                chart.setTitle(null, {
                    text: `<b>Min</b>: ${Math.min(...min)} %, 
                        <b>Max:</b> ${Math.max(...max)} %, 
                        <b>Avg:</b>${Math.max(...avg)} `
                });
            }

            chart.redraw();
            set_chart_data('timeOutHdlr', setTimeout(function () {
                requestData({target: chart});
            }, 60000));
        },
        cache: false
    });
}

function build_chart(containerId, chartOptions) {
    let chart = null;
    let $chartElem = $(containerId);
    if (!$chartElem) {
        return;
    }
    let clearChartTimeout = function () {
        let timeOutHdlr = $chartElem.data('timeOutHdlr');
        if (timeOutHdlr) {
            clearTimeout(timeOutHdlr);
        }
    };
    $chartElem.on('shiftDateChanged', function (e, fromDate, toDate, query) {
        let offset = $chartElem.data('timezoneOffset');
        if (offset) {
            // we now server timezone offset so we can use datetime
            $chartElem.data('from', new Date(fromDate.getTime() + offset).getTime() / 1000);
            $chartElem.data('to', new Date(toDate.getTime() + offset).getTime() / 1000);
        } else {
            // reset
            $chartElem.data('from', null);
            $chartElem.data('to', null);
        }
        if (query) {
            $.each(query, (key, value) => $chartElem.data(key, value));
        }
        if (!chart) {
            chart = Highcharts.chart($chartElem[0].id, chartOptions);
        } else {
            clearChartTimeout();
            requestData({target: chart});
        }
    });

    $chartElem.on('destroy', function () {
        clearChartTimeout();
        if (chart) {
            chart.destroy();
        }
        $chartElem.off('shiftDateChanged');
        $chartElem.off('destroy');
        $chartElem.parent().remove();
    });
    return $chartElem;
}


function shiftDate(hours, days, date) {
    let res = Object.prototype.toString.call(date) === '[object Date]' ? new Date(date) : new Date();
    if (hours) {
        res.setHours(res.getHours() - hours);
    }
    if (days) {
        res.setDate(res.getDate() - days);
    }
    return res;
}

Highcharts.setOptions({
    time: {
        useUTC: false
    },
    exporting: {

        buttons: {
            contextButton: {
                x: -30
            },
            'closeBtn': {
                id: 'closeBtn',
                symbol: 'cross',
                x: -5,
                onclick: function (e) {
                    let chartContainer = $(e.target).closest('.highcharts-container ');
                    if (chartContainer && chartContainer.parent()) {
                        chartContainer.parent().trigger("destroy");
                    }
                },
                title: "Close"
            }
        }
    },
})

Highcharts.SVGRenderer.prototype.symbols.cross = function (x, y, w, h, d) {

    // I want to be able to access the series data from here.
    // Either the point data or the entire series' data array.
    //if (d.v) {
    //    console.debug("Point-specific data: " + d.v);
    //}

    // From here, you can imagine one can use the point-specific data to affect the symbol path.
    // A good example would be to in case you want to build a series of custom wind barbs,
    // in which the path of the barb will be based on the intensity and direction of each point
    // ...

    return ['M', x, y, 'L', x + w, y + h, 'M', x + w, y, 'L', x, y + h, 'z'];
};

if (Highcharts.VMLRenderer) {
    Highcharts.VMLRenderer.prototype.symbols.cross = Highcharts.SVGRenderer.prototype.symbols.cross;
}

function memoryChartOption(title, shortTitle) {
    let shortTitle_ = shortTitle || title;
    return {
        chart: {
            type: 'spline',
            animation: Highcharts.svg, // don't animate in old IE
            marginRight: 10,
            events: {load: requestData},
            zoomType: 'x'
        },
        tooltip: {
            formatter: function () {
                return bytes(this.y, true);
            }
        },
        title: {
            text: title
        },
        subtitle: {
            text: document.ontouchstart === undefined ?
                'Click and drag in the plot area to zoom in' : 'Pinch the chart to zoom in'
        },
        xAxis: {
            type: 'datetime'
        },
        yAxis: {
            min: 0,
            title: {
                text: shortTitle_
            },
            labels: {
                formatter: function () {
                    return bytes(this.value, true);
                }
            }
        },
        legend: {
            enabled: true
        },
        plotOptions: {
            turboThreshold: 50000,
        },
        credits: {
            enabled: false
        },
        series: []
    };
}

function simpleChartOptions(title, shortTitle) {
    let shortTitle_ = shortTitle || title;
    return {
        chart: {
            type: 'spline',
            animation: Highcharts.svg, // don't animate in old IE
            marginRight: 10,
            events: {load: requestData},
            zoomType: 'x'
        },

        title: {
            text: title
        },
        subtitle: {
            text: document.ontouchstart === undefined ?
                'Click and drag in the plot area to zoom in' : 'Pinch the chart to zoom in'
        },
        xAxis: {
            type: 'datetime'
        },
        yAxis: {
            title: {
                text: shortTitle_
            }
        },
        legend: {
            enabled: true
        },
        plotOptions: {
            turboThreshold: 50000,
        },
        credits: {
            enabled: false
        },

        series: []
    };
}

function cpuChartOptions(title, shortTitle) {
    let options = simpleChartOptions(title, shortTitle);
    options.yAxis.min = 0;
    options.yAxis.max = 100;
    return options;
}

function timeRangeChange(graph) {
    let el = graph || $('.graph-stats');
    let shiftDateBtnGroup = $('#time-shift button.active')
    let date = new Date();
    let data = shiftDateBtnGroup.data();
    el.trigger(
        "shiftDateChanged",
        [
            shiftDate(data['shiftHours'], data['shiftDays'], date),
            date,
            {
                'fromMin': data['shiftMin'] || null,
                'fromHours': data['shiftHours'] || null,
                'fromDays': data['shiftDays'] || null,
                'fromWeek': data['shiftWeek'] || null,
            }
        ]
    );
}

$(function () {

    let mainContainer = $('main');
    let addChart = function (id, data = {}) {
        let $chartElem = $(`<div id="${id}" class="graph-stats bd-highlight border"></div>`);
        $.each(data, (key, value) => $chartElem.data(key, value));
        mainContainer.append($chartElem);
        $chartElem.wrap('<article></article>');
        return $chartElem;
    };

    let chartMap = {
        '#cpu': {
            container: 'cpu_container',
            data: {
                'calc-min-max': "1",
                'label-prefix': "CPU ",
                'url': "/cpu"
            },
            chart_options: cpuChartOptions('CPU usage')
        },
        '#per_cpu': {
            container: 'per_cpu_container',
            data: {
                'calc-min-max': "1",
                'label-prefix': "CPU ",
                'url': "/per_cpu"
            },
            chart_options: cpuChartOptions('CPU(per cpu) usage', 'CPU usage')
        },
        '#memory': {
            container: 'physical_mem_container',
            data: {
                'label-prefix': "",
                'url': "/physical_mem"
            },
            chart_options: memoryChartOption('Memory usage')
        },
        '#swap_memory': {
            container: 'swap_mem_container',
            data: {
                'label-prefix': "",
                'url': "/swap_mem"
            },
            chart_options: memoryChartOption('SWAP usage')
        },
        '#diskio': {
            container: 'disk_io_container',
            data: {
                'label-prefix': "",
                'url': "/disk_io",
                'hidden-on-start': "read_count,write_count,read_time,write_time,busy_time"
            },
            chart_options: memoryChartOption('Disk IO')
        },
        '#tomcat_cpu': {
            container: 'tomcat_cpu_container',
            data: {
                'calc-min-max': "1",
                'label-prefix': "",
                'url': "/tomcat_cpu_utilization"
            },
            chart_options: cpuChartOptions('Tomcat CPU usage', 'CPU usage')
        },
        '#tomcat_diskio': {
            container: 'tomcat_diskio_container',
            data: {
                'label-prefix': "",
                'url': "/tomcat_disk_io_utilization"
            },
            chart_options: memoryChartOption('Tomcat Disk IO usage')
        },
        '#tomcat_memory': {
            container: 'tomcat_memory_utilization_container',
            data: {
                'label-prefix': "",
                'url': "/tomcat_memory_utilization"
            },
            chart_options: memoryChartOption('Tomcat Memory usage')
        },
        '#tomcat_sockets': {
            container: 'tomcat_conn_utilization_container',
            data: {
                'label-prefix': "",
                'url': "/tomcat_conn_utilization"
            },
            chart_options: simpleChartOptions('Tomcat Socket usage')
        },
        '#tomcat_other': {
            container: 'tomcat_other_utilization_container',
            data: {
                'label-prefix': "",
                'url': "/tomcat_other_utilization"
            },
            chart_options: simpleChartOptions('Tomcat Other usage')
        },
        '#imap_cpu': {
            container: 'imap_cpu_container',
            data: {
                'calc-min-max': "1",
                'label-prefix': "",
                'url': "/imap_cpu_utilization"
            },
            chart_options: cpuChartOptions('Imap CPU usage', 'CPU usage')
        },
        '#imap_diskio': {
            container: 'imap_diskio_container',
            data: {
                'label-prefix': "",
                'url': "/imap_disk_io_utilization"
            },
            chart_options: memoryChartOption('Imap Disk IO usage')
        },
        '#imap_memory': {
            container: 'Imap_memory_utilization_container',
            data: {
                'label-prefix': "",
                'url': "/imap_memory_utilization"
            },
            chart_options: memoryChartOption('Imap Memory usage')
        },
        '#imap_sockets': {
            container: 'imap_conn_utilization_container',
            data: {
                'label-prefix': "",
                'url': "/imap_conn_utilization"
            },
            chart_options: simpleChartOptions('Imap Socket usage')
        },
        '#imap_other': {
            container: 'imap_other_utilization_container',
            data: {
                'label-prefix': "",
                'url': "/imap_other_utilization"
            },
            chart_options: simpleChartOptions('Imap Other usage')
        },
    };

    // Dropdown menu
    $(".sidebar-menu").on('click', 'a', function () {
        //$(".sidebar-submenu").slideUp(200);
        let $this = $(this);
        let $category = $this.closest('li.category');

        $(".sidebar-submenu:visible").each((indx, elem) => {
            if ($(elem).closest('li.category')[0] != $category[0]) {
                $(elem).slideUp(200);
            }
        });
        let $submenu = $(".sidebar-submenu", $this.parent());

        if ($submenu.length > 0) {
            $submenu.slideDown(200);
            return false;
        }
        let isActiveCat = $category.hasClass('active');

        if ($this.data('clear') !== undefined) {
            if (getBoolean($this.data('clear'))) {
                $('.graph-stats').trigger('destroy');
            }
        } else if (getBoolean($category.data('clear')) && !isActiveCat) {
            $('.graph-stats').trigger('destroy');
        }

        if (!isActiveCat) {
            $(".sidebar-dropdown").removeClass("active");
            $category.addClass('active');

        }

        let data = chartMap[$this[0].hash];
        if (data) {
            let containerId = '#' + data.container;
            if ($(containerId).length > 0) {
                $('html, body').animate(
                    {scrollTop: $(containerId).offset().top},
                    100
                );
                return;
            }
            addChart(data.container, data.data);
            timeRangeChange(build_chart(containerId, data.chart_options));
            $('html, body').animate(
                {scrollTop: $(containerId).offset().top},
                100
            );
        }
    });

    $("#sidebar").hover(
        function () {
            $(".sidebar-submenu").slideUp(200);
            $(".page-wrapper").addClass("sidebar-hovered");
        },
        function () {
            $(".page-wrapper").removeClass("sidebar-hovered");
        }
    );

    //custom scroll bar is only used on desktop
    if (!/Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent)) {
        $(".sidebar-content").mCustomScrollbar({
            axis: "y",
            autoHideScrollbar: true,
            scrollInertia: 300
        });
        $(".sidebar-content").addClass("desktop");
    }
    ;

    $(document).on('click', 'details', function () {
        $(this).toggleClass("border border-warning");
    });

    let timeShitBtns = $('#time-shift button')
    timeShitBtns.on('click', function () {
        timeShitBtns.removeClass('active');
        $(this).addClass('active');
        timeRangeChange();
    });

    $('li a[href="#cpu"], li a[href="#memory"]').trigger('click');
    $('#time-shift button:first').trigger('click');
})