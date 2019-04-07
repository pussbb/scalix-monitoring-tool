$(function () {


    let options = function () {
        return {
            chart: {
                type: 'spline',
                animation: Highcharts.svg, // don't animate in old IE
                marginRight: 10,
                events: {load: requestData},
                zoomType: 'x'
            },

            title: {
                text: 'CPU(per cpu) usage'
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
                max: 100,
                title: {
                    text: 'CPU usage'
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

    };
    build_chart('#per_cpu_container', options());
    let cpu_options = options();
    cpu_options.title.text = 'CPU usage';
    build_chart('#cpu_container', cpu_options);

});