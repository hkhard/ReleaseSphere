function loadDateFns() {
    return new Promise((resolve, reject) => {
        if (typeof dateFns === 'undefined') {
            console.log('date-fns library not found, loading dynamically');
            const script = document.createElement('script');
            script.src = 'https://cdnjs.cloudflare.com/ajax/libs/date-fns/2.29.3/date-fns.min.js';
            script.onload = () => resolve();
            script.onerror = () => reject(new Error('Failed to load date-fns'));
            document.head.appendChild(script);
        } else {
            console.log('date-fns library found');
            resolve();
        }
    });
}

loadDateFns()
    .then(() => {
        console.log('date-fns loaded, initializing dashboard');
        initializeDashboard();
    })
    .catch(error => {
        console.error('Error loading date-fns:', error);
    });

let svg, xScale, yScale;
const margin = { top: 20, right: 20, bottom: 30, left: 40 };
const width = 960 - margin.left - margin.right;
const height = 500 - margin.top - margin.bottom;

function initializeDashboard() {
    function initializeSVG() {
        console.log("Initializing SVG");
        svg = d3.select("#timeline")
            .append("svg")
            .attr("width", width + margin.left + margin.right)
            .attr("height", height + margin.top + margin.bottom)
            .append("g")
            .attr("transform", `translate(${margin.left},${margin.top})`);
    }

    function setAttributeSafe(element, attribute, value) {
        if (!isNaN(value) && isFinite(value)) {
            element.setAttribute(attribute, value);
        } else {
            console.error(`Invalid value for ${attribute}:`, value);
        }
    }

    function createScales(data) {
        console.log("Creating scales with data:", data);
        if (!data.epics && !data.features && !data.sprints) {
            console.error("Invalid data structure. Missing epics, features, and sprints.");
            return false;
        }

        const allItems = [
            ...(data.epics || []),
            ...(data.features || []),
            ...(data.sprints || [])
        ];

        const allDates = allItems
            .flatMap(item => [item.startDate, item.endDate])
            .filter(date => date != null && date !== "");
        
        console.log("All date strings before parsing:", allDates);

        const parsedDates = allDates
            .map(dateString => {
                try {
                    const parsed = dateFns.parseISO(dateString);
                    console.log(`Parsing date string: ${dateString}, Result: ${parsed}`);
                    return parsed;
                } catch (error) {
                    console.error(`Error parsing date: ${dateString}`, error);
                    return null;
                }
            })
            .filter(date => {
                try {
                    const isValidDate = dateFns.isValid(date);
                    console.log(`Validating date: ${date}, Is valid: ${isValidDate}`);
                    return isValidDate;
                } catch (error) {
                    console.error(`Error validating date: ${date}`, error);
                    return false;
                }
            });

        if (parsedDates.length === 0) {
            console.error("No valid dates found in the data");
            return false;
        }

        const minDate = d3.min(parsedDates);
        const maxDate = d3.max(parsedDates);

        console.log("Min date:", minDate);
        console.log("Max date:", maxDate);

        xScale = d3.scaleTime()
            .domain([minDate, maxDate])
            .range([0, width]);

        yScale = d3.scaleBand()
            .domain(allItems.map(d => d.name))
            .range([0, height])
            .padding(0.1);

        return true;
    }

    function fetchReleasePlan() {
        console.log("Fetching release plan data");
        fetch('/api/release_plan')
            .then(response => response.json())
            .then(data => {
                console.log("Fetched release plan data:", data);
                if (!data || (!data.epics && !data.features && !data.sprints)) {
                    console.error("Invalid or empty data received from the server");
                    return;
                }
                renderTimeline(data);
            })
            .catch(error => {
                console.error('Error fetching release plan:', error);
            });
    }

    initializeSVG();
    fetchReleasePlan();
}

function renderTimeline(data) {
    console.log("Rendering timeline with data:", data);

    svg.selectAll("*").remove();
    if (!createScales(data)) {
        console.error("Failed to create scales. Aborting render.");
        return;
    }

    // Render epics
    if (data.epics) renderItems(data.epics, "epic");

    // Render features
    if (data.features) renderItems(data.features, "feature");

    // Render sprints
    if (data.sprints) renderItems(data.sprints, "sprint");

    // Add x-axis
    svg.append("g")
        .attr("transform", `translate(0,${height})`)
        .call(d3.axisBottom(xScale));

    // Add y-axis
    svg.append("g")
        .call(d3.axisLeft(yScale));
}

function renderItems(items, className) {
    console.log(`Rendering ${className}s:`, items);
    const itemGroups = svg.selectAll(`.${className}`)
        .data(items)
        .enter()
        .append("g")
        .attr("class", className);

    itemGroups.each(function(d) {
        const group = d3.select(this);
        console.log(`Processing ${className}:`, d.name, "Start:", d.startDate, "End:", d.endDate);
        
        if (!d.startDate || !d.endDate) {
            console.error(`Missing date for ${className}:`, d.name, "Start:", d.startDate, "End:", d.endDate);
            return;
        }

        let startDate, endDate;
        try {
            startDate = dateFns.parseISO(d.startDate);
            endDate = dateFns.parseISO(d.endDate);
        } catch (error) {
            console.error(`Error parsing dates for ${className}:`, d.name, error);
            return;
        }
        
        console.log(`Parsed dates - Start: ${startDate}, End: ${endDate}`);
        
        if (!dateFns.isValid(startDate) || !dateFns.isValid(endDate)) {
            console.error(`Invalid date for ${className}:`, d.name, "Start:", d.startDate, "End:", d.endDate);
            return;
        }

        console.log(`Rendering ${className}:`, d.name, "Start:", dateFns.format(startDate, 'yyyy-MM-dd'), "End:", dateFns.format(endDate, 'yyyy-MM-dd'));

        const x = xScale(startDate);
        const y = yScale(d.name);
        const width = xScale(endDate) - xScale(startDate);
        const height = yScale.bandwidth();

        console.log(`Calculated values - x: ${x}, y: ${y}, width: ${width}, height: ${height}`);

        const rect = group.append("rect");
        setAttributeSafe(rect.node(), "x", x);
        setAttributeSafe(rect.node(), "y", y);
        setAttributeSafe(rect.node(), "width", width);
        setAttributeSafe(rect.node(), "height", height);
        rect.attr("class", className);

        const text = group.append("text");
        setAttributeSafe(text.node(), "x", x + 5);
        setAttributeSafe(text.node(), "y", y + height / 2);
        text.attr("dy", ".35em")
            .text(d.name);
    });
}

function applyFilters() {
    const viewType = document.getElementById('view-type').value;
    const searchFilter = document.getElementById('search-filter').value;

    fetch('/api/customize_view', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            view_type: viewType,
            filters: {
                name: searchFilter
            }
        }),
    })
    .then(response => response.json())
    .then(data => {
        // Update the timeline with the filtered data
        if (typeof renderTimeline === 'function') {
            renderTimeline(data);
        } else {
            console.error('renderTimeline function is not defined');
        }
    })
    .catch(error => {
        console.error('Error applying filters:', error);
    });
}
