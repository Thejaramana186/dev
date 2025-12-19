document.addEventListener("DOMContentLoaded", async () => {

    const chartContainer = document.getElementById("niftyChart");

    const chart = LightweightCharts.createChart(chartContainer, {
        width: chartContainer.clientWidth,
        height: 500,
        layout: {
            background: { color: '#ffffff' },
            textColor: '#000',
        },
        grid: {
            vertLines: { color: '#eee' },
            horzLines: { color: '#eee' },
        },
        timeScale: {
            timeVisible: true,
            secondsVisible: false,
        }
    });

    const candleSeries = chart.addCandlestickSeries({
        upColor: '#26a69a',
        downColor: '#ef5350',
        borderUpColor: '#26a69a',
        borderDownColor: '#ef5350',
        wickUpColor: '#26a69a',
        wickDownColor: '#ef5350',
    });

    try {
        const res = await fetch("/api/nifty");
        const rawData = await res.json();

        const formattedData = rawData.map(d => {
            const date = new Date(d.time * 1000);
            return {
                  time: d.time,
                open: d.open,
                high: d.high,
                low: d.low,
                close: d.close
            };
        });

        candleSeries.setData(formattedData);
        chart.timeScale().fitContent();

    } catch (err) {
        console.error("Failed to load NIFTY chart", err);
    }

   
    window.addEventListener("resize", () => {
        chart.applyOptions({
            width: chartContainer.clientWidth
        });
    });
});
``