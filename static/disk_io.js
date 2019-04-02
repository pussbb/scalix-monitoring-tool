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
            /*tooltip: {
                    formatter: function(){
                        if (['read_bytes', 'write_bytes'].includes(this.series.name)) {
                            return this.series.name + ' ' + bytes(this.y, true);
                        } else if (['read_time', 'write_time', 'busy_time'].includes(this.series.name)) {
                            return this.series.name + ' ' +  this.y + ' ms.';
                        } else {
                            return this.series.name + ' ' +  this.y;
                        }
                    }
                },*/

            title: {
                text: 'Disk IO usage'
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
                    text: 'DISK IO usage'
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


    build_chart('#disk_io_container', options());

});