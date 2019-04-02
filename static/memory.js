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
                       return bytes(this.y, true);
                    }
                },
            title: {
                text: 'Memory usage'
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
                    text: 'Memory usage'
                },
                labels: {
                    formatter: function() {
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
    };



    build_chart('#physical_mem_container', options());
    let swap_options = options();
    swap_options.title.text = 'SWAP usage';
    build_chart('#swap_mem_container', swap_options);

});