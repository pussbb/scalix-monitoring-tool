function prepData(data) {
    return data.map(item => {
        return [Date.parse(item[0]), parseFloat(item[1])]
    })
};

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

    $(document).on('destroy-' + $chartElem.attr('id'), function () {
        clearChartTimeout();
        if (chart) {
            chart.destroy();
        }
        if ($chartElem) {
            $chartElem.off('shiftDateChanged');
            $(document).off('destroy-' + $chartElem.attr('id'));
            $chartElem.parent().remove();
        }
    });
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
                    let mainContainer = $(e.target).closest('.highcharts-container ').parent();
                    $(document).trigger("destroy-" + mainContainer.attr('id'));
                },
                title: "Close"
            }
        }
    },
});

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


$(function () {
    // Dropdown menu
    $(".sidebar-dropdown > a").click(function () {
        $(".sidebar-submenu").slideUp(200);
        if ($(this).parent().hasClass("active")) {
            $(".sidebar-dropdown").removeClass("active");
            $(this).parent().removeClass("active");
        } else {
            $(".sidebar-dropdown").removeClass("active");
            $(this).next(".sidebar-submenu").slideDown(200);
            $(this).parent().addClass("active");
        }

    });

    $("#sidebar").hover(
        function () {
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
        let date = new Date();
        let data = $(this).data();
        $('.graph-stats').trigger(
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
    });
    $('#time-shift button:first').click()
})