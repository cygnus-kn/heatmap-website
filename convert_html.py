import os
import json
import sqlite3

# 1. Build steps_data.js
db_path = "/Users/cygnus/Documents/GitHub/Sleep-Data/health_connect_export.db"
out_path = "/Users/cygnus/Documents/GitHub/heatmap-website/steps_data.js"

conn = sqlite3.connect(db_path)
c = conn.cursor()
c.execute("""
    SELECT date(start_time/1000, 'unixepoch', 'localtime'), sum(count) 
    FROM steps_record_table 
    GROUP BY date(start_time/1000, 'unixepoch', 'localtime')
""")

data = {}
for row in c.fetchall():
    date_str, count = row
    if date_str:
        data[date_str] = count

js_content = f"const stepsData = {json.dumps(data)};"
with open(out_path, "w") as f:
    f.write(js_content)
    
# 2. Add step_data.js to index.html and duplicate the heatmap section
index_path = "/Users/cygnus/Documents/GitHub/heatmap-website/index.html"
with open(index_path, "r") as f:
    html = f.read()

# Replace script tag
html = html.replace('<script src="data.js"></script>', '<script src="data.js"></script>\n    <script src="steps_data.js"></script>')

# Replace body tag and first container start to have margin-bottom
html = html.replace('<body>\n\n    <div class="container">', '<body>\n\n    <div class="container" style="margin-bottom: 2rem;">')

# Insert the second container into the HTML before the tooltip
steps_container_html = """

    <div class="container">
        <header>
            <div>
                <h1 id="steps-h1">Daily Steps Heatmap</h1>
                <div class="subtitle">Track your physical activity</div>
            </div>
            <div class="controls">
                <select id="steps-year-selector"></select>
            </div>
        </header>

        <div class="heatmap-wrapper">
            <div class="day-labels">
                <span class="day-label">Mon</span>
                <span class="day-label">Tue</span>
                <span class="day-label">Wed</span>
                <span class="day-label">Thu</span>
                <span class="day-label">Fri</span>
                <span class="day-label">Sat</span>
                <span class="day-label">Sun</span>
            </div>
            <div class="heatmap-container">
                <div class="month-labels" id="steps-month-labels"></div>
                <div class="heatmap" id="steps-heatmap"></div>
            </div>
        </div>

        <div class="footer">
            <div class="stats-group">
                <div class="stat-item">Total steps: <strong id="steps-stat-total">0</strong></div>
                <div class="stat-item">Days active: <strong id="steps-stat-days">0</strong></div>
                <div class="stat-item">Average steps: <strong id="steps-stat-max">0</strong></div>
            </div>
            <div class="legend">
                <span>Less</span>
                <div class="legend-squares" id="steps-legend">
                    <div class="square" data-level="0"></div>
                    <div class="square" data-level="1"></div>
                    <div class="square" data-level="2"></div>
                    <div class="square" data-level="3"></div>
                    <div class="square" data-level="4"></div>
                    <div class="square" data-level="5"></div>
                </div>
                <span>More</span>
            </div>
        </div>
    </div>
"""
html = html.replace('    <div class="tooltip" id="tooltip"></div>', steps_container_html + '\n    <div class="tooltip" id="tooltip"></div>')

# Now replace the entire <script> content
start_script = html.find('<script>') + len('<script>')
end_script = html.rfind('</script>')
new_script = """
        const tooltip = document.getElementById('tooltip');

        function initHeatmap(data, selectorId, heatmapId, monthLabelsId, statTotalId, statDaysId, statMaxId, countLabel, themePrefix = '--color-l', statMode = 'max', customThresholds = null) {
            const rawDates = Object.keys(data).sort();
            const years = [...new Set(rawDates.map(date => date.split('-')[0]))];
            
            const selector = document.getElementById(selectorId);
            const heatmapEl = document.getElementById(heatmapId);
            const monthLabelsEl = document.getElementById(monthLabelsId);
            const statTotal = document.getElementById(statTotalId);
            const statDays = document.getElementById(statDaysId);
            const statMax = document.getElementById(statMaxId);

            if (years.length === 0) {
                years.push(new Date().getFullYear().toString());
            }

            years.reverse().forEach(y => {
                const opt = document.createElement('option');
                opt.value = y;
                opt.textContent = y;
                selector.appendChild(opt);
            });

            selector.addEventListener('change', (e) => {
                render(e.target.value);
            });

            function render(year) {
                heatmapEl.innerHTML = '';
                monthLabelsEl.innerHTML = '';
                
                const yearData = {};
                let maxCount = 0;
                let totalCount = 0;
                let daysActive = 0;
                
                for (const [date, info] of Object.entries(data)) {
                    if (date.startsWith(year)) {
                        let count = typeof info === 'number' ? info : (info.count || 0);
                        let title = typeof info === 'number' ? '' : (info.title || '');
                        let path = typeof info === 'number' ? '' : (info.path || '');
                        
                        yearData[date] = { count, title, path };
                        totalCount += count;
                        daysActive++;
                        if (count > maxCount) maxCount = count;
                    }
                }

                let avgCount = daysActive > 0 ? Math.round(totalCount / daysActive) : 0;
                statTotal.textContent = totalCount.toLocaleString();
                statDays.textContent = daysActive;
                statMax.textContent = (statMode === 'avg' ? avgCount : maxCount).toLocaleString();

                const counts = Object.values(yearData).map(d => d.count).filter(c => c > 0).sort((a,b) => a-b);
                let q1=0, q2=0, q3=0, q4=0;
                if (counts.length > 0) {
                    q1 = counts[Math.floor(counts.length * 0.20)] || 1;
                    q2 = counts[Math.floor(counts.length * 0.40)] || 1;
                    q3 = counts[Math.floor(counts.length * 0.60)] || 1;
                    q4 = counts[Math.floor(counts.length * 0.80)] || 1;
                }

                function getLevel(c) {
                    if (c === 0) return 0;
                    if (customThresholds) {
                        for (let i = customThresholds.length - 1; i >= 0; i--) {
                            if (c >= customThresholds[i]) return i + 2;
                        }
                        return 1;
                    }
                    if (c <= q1) return 1;
                    if (c <= q2) return 2;
                    if (c <= q3) return 3;
                    if (c <= q4) return 4;
                    return 5;
                }

                const startDate = new Date(`${year}-01-01T00:00:00`);
                const endDate = new Date(`${year}-12-31T00:00:00`);
                
                let startDay = startDate.getDay() - 1;
                if (startDay === -1) startDay = 6;
                
                for (let i = 0; i < startDay; i++) {
                    const emptySquare = document.createElement('div');
                    emptySquare.className = 'square';
                    emptySquare.style.visibility = 'hidden';
                    heatmapEl.appendChild(emptySquare);
                }

                let currentDate = new Date(startDate);
                let colIndex = 0;
                let currentMonth = -1;
                const months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
                let delay = 0;

                while (currentDate <= endDate) {
                    if (currentDate.getMonth() !== currentMonth) {
                        currentMonth = currentDate.getMonth();
                        const monthLabel = document.createElement('span');
                        monthLabel.className = 'month-label';
                        monthLabel.textContent = months[currentMonth];
                        monthLabel.style.left = `calc(${colIndex} * (var(--square-size) + var(--square-gap)))`;
                        monthLabelsEl.appendChild(monthLabel);
                    }

                    const dateStr = currentDate.toISOString().split('T')[0];
                    const dateData = yearData[dateStr] || { count: 0, title: '', path: '' };
                    const count = dateData.count;
                    const noteTitle = dateData.title || dateStr;
                    const notePath = dateData.path || '';
                    const level = getLevel(count);

                    const square = document.createElement('div');
                    square.className = 'square';
                    square.setAttribute('data-level', level);
                    square.style.animationDelay = `${delay}s`;
                    
                    if (count > 0 && notePath !== '') {
                        square.addEventListener('click', () => {
                            window.location.href = `note.html?file=${encodeURIComponent(notePath)}`;
                        });
                    }
                    
                    square.addEventListener('mouseenter', () => {
                        const rect = square.getBoundingClientRect();
                        const levelColors = {
                            0: "var(--text-main)",
                            1: `var(${themePrefix}1)`,
                            2: `var(${themePrefix}2)`,
                            3: `var(${themePrefix}3)`,
                            4: `var(${themePrefix}4)`,
                            5: `var(${themePrefix}5)`
                        };
                        const countColor = levelColors[level];

                        const text = count === 0 
                            ? `No records on ${dateStr}`
                            : (notePath !== '' ? `<div style="margin-bottom: 4px; border-bottom: 1px solid rgba(255,255,255,0.1); padding-bottom: 4px; white-space: normal; max-width: 250px;"><strong>${noteTitle}</strong></div>` : '') + `<span class="count" style="color: ${countColor};">${count.toLocaleString()}</span> ${countLabel}`;
                        
                        tooltip.innerHTML = text;
                        tooltip.classList.add('show');
                        
                        const topPos = rect.top + window.scrollY;
                        const leftPos = rect.left + window.scrollX + (rect.width / 2);
                        
                        tooltip.style.left = `${leftPos}px`;
                        tooltip.style.top = `${topPos}px`;
                    });

                    square.addEventListener('mouseleave', () => {
                        tooltip.classList.remove('show');
                    });

                    heatmapEl.appendChild(square);
                    currentDate.setDate(currentDate.getDate() + 1);
                    if (currentDate.getDay() === 1) colIndex++;
                    delay += 0.001;
                }
            }
            if (years.length > 0) render(years[0]);
        }
        
        const noteData = typeof heatmapData !== 'undefined' ? heatmapData : {};
        const stepData = typeof stepsData !== 'undefined' ? stepsData : {};

        initHeatmap(noteData, 'year-selector', 'heatmap', 'month-labels', 'stat-total', 'stat-days', 'stat-max', 'words', '--color-l', 'max');
        initHeatmap(stepData, 'steps-year-selector', 'steps-heatmap', 'steps-month-labels', 'steps-stat-total', 'steps-stat-days', 'steps-stat-max', 'steps', '--steps-color-l', 'avg', [2000, 4000, 6000, 8000]);
"""
html = html[:start_script] + new_script + html[end_script:]

with open(index_path, "w") as f:
    f.write(html)
