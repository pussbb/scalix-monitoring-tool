$(function () {


    let options = function() {
        return {
            chart: {
                type: 'spline',
                animation: Highcharts.svg, // don't animate in old IE
                marginRight: 10,
                events: {load: requestData},
                zoomType: 'x'
            },
            tooltip: {
                    formatter: function(){
                        if (this.series.name
                            && (this.series.name.lastIndexOf('disk') >= 0
                                || this.series.name.lastIndexOf('memory'))>= 0) {
                            return bytes(this.y, true);
                        }
                        return this.y;
                    }
                },
            title: {
                text: 'Tomcat utilization'
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
                    text: 'Tomcat utilization'
                },
                labels: {
                    formatter: function() {
                        return this.value;
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
    };



    build_chart('#tomcat_utilization_container', options());
    let swap_options = options();
    swap_options.title.text = 'Tomcat Utilization additional';
    swap_options.yAxis.title.text = 'Tomcat Utilization additional';
    build_chart('#tomcat_other_container', swap_options);

    let imap_options = options();
    imap_options.title.text = 'Imap Utilization';
    imap_options.yAxis.title.text = 'Imap Utilization';
    build_chart('#imap_utilization_container', imap_options);

    let imap_other_options = options();
    imap_other_options.title.text = 'Imap Utilization Additional';
    imap_other_options.yAxis.title.text = 'Imap Utilization Additional';
    build_chart('#imap_other_container', imap_other_options);

});