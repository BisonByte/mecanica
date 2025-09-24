const { Chart } = window;

const STORAGE_KEY = 'mechanics.beam.config.v2';
const STEP_ORDER = ['geometria', 'apoyos', 'cargas', 'opciones', 'resultados'];

const state = {
    defaults: {},
    pointLoads: [],
    distributedLoads: [],
    charts: {},
    busy: false,
    autoAnalyze: true,
    lastResult: null,
};

const elements = {
    form: document.getElementById('beam-form'),
    stepper: document.getElementById('form-stepper'),
    stepButtons: Array.from(document.querySelectorAll('[data-step]')),
    stepPanels: Array.from(document.querySelectorAll('[data-step-panel]')),
    length: document.getElementById('length'),
    heightStart: document.getElementById('height_start'),
    heightEnd: document.getElementById('height_end'),
    torsor: document.getElementById('torsor'),
    supportA: document.getElementById('support_a_type'),
    supportB: document.getElementById('support_b_type'),
    supportC: document.getElementById('support_c_type'),
    supportCPos: document.getElementById('support_c_position'),
    supportCGroup: document.getElementById('support_c_position_group'),
    numPoints: document.getElementById('num_points'),
    unitSystem: document.getElementById('unit_system'),
    exportFormat: document.getElementById('export_format'),
    autoAnalyze: document.getElementById('auto-analyze'),
    pointList: document.getElementById('point-loads'),
    distributedList: document.getElementById('distributed-loads'),
    addPoint: document.getElementById('add-point-load'),
    addDistributed: document.getElementById('add-distributed-load'),
    reset: document.getElementById('reset-form'),
    feedback: document.getElementById('form-feedback'),
    reactionsCards: document.querySelectorAll('#reactions-summary [data-reaction]'),
    equilibrium: document.getElementById('equilibrium-summary'),
    centerOfMass: document.getElementById('center-of-mass'),
    loadsDetail: document.getElementById('loads-detail'),
    templateList: document.getElementById('template-list'),
    reloadTemplates: document.getElementById('reload-templates'),
    exportJson: document.getElementById('export-json'),
    insights: document.getElementById('analysis-insights'),
    projectSummary: document.getElementById('project-summary'),
};

const palette = {
    primary: cssVar('--color-primary'),
    accent: cssVar('--color-accent'),
    warning: '#f97316',
};

if (typeof Chart === 'undefined') {
    console.error('Chart.js no se cargó correctamente.');
}

init();

function init() {
    const defaults = deepCopy(window.__DEFAULT_PAYLOAD__ || {});
    const persisted = loadState();

    state.defaults = deepCopy(defaults);
    const initial = persisted || defaults;

    hydrateState(initial);
    populateForm(initial);
    renderPointLoads();
    renderDistributedLoads();
    activateStep('geometria');
    attachEvents();
    toggleSupportCField();
    fetchTemplates();
    const payload = gatherPayload();
    analyze(payload, { silent: true });
}

function hydrateState(payload) {
    state.pointLoads = deepCopy(payload.point_loads || []);
    state.distributedLoads = deepCopy(payload.distributed_loads || []);
    state.autoAnalyze = payload.auto_analyze ?? true;
}

function attachEvents() {
    elements.addPoint.addEventListener('click', () => {
        state.pointLoads.push({ label: '', position: 0, magnitude: 10 });
        renderPointLoads();
        persistAndMaybeAnalyze();
    });

    elements.addDistributed.addEventListener('click', () => {
        state.distributedLoads.push({ label: '', start: 0, end: 1, intensity: 5 });
        renderDistributedLoads();
        persistAndMaybeAnalyze();
    });

    elements.supportC.addEventListener('change', () => {
        toggleSupportCField();
        persistAndMaybeAnalyze();
    });

    elements.reset.addEventListener('click', () => {
        resetToDefaults();
        setFeedback('Se restauraron los valores iniciales.');
    });

    elements.autoAnalyze.addEventListener('change', () => {
        state.autoAnalyze = elements.autoAnalyze.checked;
        persistAndMaybeAnalyze();
    });

    elements.form.addEventListener('input', (event) => {
        const target = event.target;
        if (target === elements.supportCPos && (elements.supportC.value || '').toLowerCase() === 'ninguno') {
            return;
        }
        persistAndMaybeAnalyze();
    });

    elements.form.addEventListener('change', (event) => {
        if (event.target.matches('select')) {
            persistAndMaybeAnalyze();
        }
    });

    elements.form.addEventListener('submit', (event) => {
        event.preventDefault();
        const payload = gatherPayload();
        analyze(payload);
        saveState(payload);
    });

    elements.stepButtons.forEach((button) => {
        button.addEventListener('click', () => activateStep(button.dataset.step));
    });

    elements.reloadTemplates.addEventListener('click', () => fetchTemplates(true));

    elements.exportJson.addEventListener('click', exportCurrentConfiguration);
}

function activateStep(step) {
    if (!step || !STEP_ORDER.includes(step)) return;

    elements.stepButtons.forEach((button) => {
        button.classList.toggle('stepper__step--active', button.dataset.step === step);
    });

    elements.stepPanels.forEach((panel) => {
        panel.classList.toggle('step--active', panel.dataset.stepPanel === step);
    });
}

function populateForm(data) {
    elements.length.value = valueOr(data.length, 10);
    elements.heightStart.value = valueOr(data.height_start, 0);
    elements.heightEnd.value = valueOr(data.height_end, 0);
    elements.supportA.value = data.support_a_type || 'Fijo';
    elements.supportB.value = data.support_b_type || 'Movil';
    elements.supportC.value = data.support_c_type || 'Ninguno';
    elements.supportCPos.value = data.support_c_position ?? '';
    elements.torsor.value = valueOr(data.torsor, 0);

    const analysis = data.analysis || {};
    elements.numPoints.value = valueOr(analysis.num_points, 800);
    elements.unitSystem.value = analysis.unit_system || 'SI';
    elements.exportFormat.value = analysis.export_format || 'json';
    elements.autoAnalyze.checked = data.auto_analyze ?? true;
}

function renderPointLoads() {
    const container = elements.pointList;
    container.innerHTML = '';

    if (!state.pointLoads.length) {
        container.appendChild(emptyState('Sin cargas puntuales.'));
        return;
    }

    state.pointLoads.forEach((load, index) => {
        const row = document.createElement('div');
        row.className = 'dynamic-item';
        row.dataset.index = String(index);
        row.innerHTML = `
            <div class="field">
                <label>Etiqueta</label>
                <input type="text" value="${escapeHtml(load.label || '')}" data-field="label" />
            </div>
            <div class="field">
                <label>Posición (m)</label>
                <input type="number" step="0.01" value="${load.position ?? 0}" data-field="position" />
            </div>
            <div class="field">
                <label>Magnitud (N)</label>
                <input type="number" step="0.01" value="${load.magnitude ?? 0}" data-field="magnitude" />
            </div>
            <button type="button" class="dynamic-item__remove" aria-label="Eliminar carga" title="Eliminar">&times;</button>
        `;

        row.addEventListener('input', (evt) => {
            handlePointLoadInput(index, evt);
            persistAndMaybeAnalyze();
        });
        row.querySelector('.dynamic-item__remove').addEventListener('click', () => {
            state.pointLoads.splice(index, 1);
            renderPointLoads();
            persistAndMaybeAnalyze();
        });

        container.appendChild(row);
    });
}

function renderDistributedLoads() {
    const container = elements.distributedList;
    container.innerHTML = '';

    if (!state.distributedLoads.length) {
        container.appendChild(emptyState('Sin cargas distribuidas.'));
        return;
    }

    state.distributedLoads.forEach((load, index) => {
        const row = document.createElement('div');
        row.className = 'dynamic-item';
        row.dataset.index = String(index);
        row.innerHTML = `
            <div class="field">
                <label>Etiqueta</label>
                <input type="text" value="${escapeHtml(load.label || '')}" data-field="label" />
            </div>
            <div class="field">
                <label>Inicio (m)</label>
                <input type="number" step="0.01" value="${load.start ?? 0}" data-field="start" />
            </div>
            <div class="field">
                <label>Fin (m)</label>
                <input type="number" step="0.01" value="${load.end ?? 0}" data-field="end" />
            </div>
            <div class="field">
                <label>Intensidad (N/m)</label>
                <input type="number" step="0.01" value="${load.intensity ?? 0}" data-field="intensity" />
            </div>
            <button type="button" class="dynamic-item__remove" aria-label="Eliminar carga distribuida" title="Eliminar">&times;</button>
        `;

        row.addEventListener('input', (evt) => {
            handleDistributedInput(index, evt);
            persistAndMaybeAnalyze();
        });
        row.querySelector('.dynamic-item__remove').addEventListener('click', () => {
            state.distributedLoads.splice(index, 1);
            renderDistributedLoads();
            persistAndMaybeAnalyze();
        });

        container.appendChild(row);
    });
}

function handlePointLoadInput(index, event) {
    const field = event.target.dataset.field;
    if (!field) return;
    const value = event.target.value;
    const load = state.pointLoads[index];
    if (!load) return;

    if (field === 'label') {
        load.label = value;
    } else {
        load[field] = numberOr(value, 0);
    }
}

function handleDistributedInput(index, event) {
    const field = event.target.dataset.field;
    if (!field) return;
    const value = event.target.value;
    const load = state.distributedLoads[index];
    if (!load) return;

    if (field === 'label') {
        load.label = value;
    } else {
        load[field] = numberOr(value, 0);
    }
}

function toggleSupportCField() {
    const active = (elements.supportC.value || 'Ninguno').toLowerCase() !== 'ninguno';
    elements.supportCGroup.style.display = active ? 'block' : 'none';
    if (!active) {
        elements.supportCPos.value = '';
    }
}

function gatherPayload() {
    const payload = {
        length: numberOr(elements.length.value, 0),
        height_start: numberOr(elements.heightStart.value, 0),
        height_end: numberOr(elements.heightEnd.value, 0),
        support_a_type: elements.supportA.value,
        support_b_type: elements.supportB.value,
        support_c_type: elements.supportC.value,
        support_c_position: null,
        torsor: numberOr(elements.torsor.value, 0),
        point_loads: state.pointLoads.map((load) => ({
            label: load.label || '',
            position: numberOr(load.position, 0),
            magnitude: numberOr(load.magnitude, 0),
        })),
        distributed_loads: state.distributedLoads.map((load) => ({
            label: load.label || '',
            start: numberOr(load.start, 0),
            end: numberOr(load.end, 0),
            intensity: numberOr(load.intensity, 0),
        })),
        analysis: {
            num_points: numberOr(elements.numPoints.value, 800),
            export_format: elements.exportFormat.value,
            unit_system: elements.unitSystem.value,
        },
        auto_analyze: state.autoAnalyze,
    };

    if ((elements.supportC.value || '').toLowerCase() !== 'ninguno') {
        payload.support_c_position = elements.supportCPos.value === '' ? null : numberOr(elements.supportCPos.value, null);
    }

    return payload;
}

async function analyze(payload, options = {}) {
    if (state.busy) return;
    state.busy = true;
    setLoading(true);
    setFeedback('Calculando…');

    try {
        const response = await fetch('/api/beam/analyze', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload),
        });
        const data = await response.json();
        if (!response.ok) {
            throw new Error(data.detail || 'Error desconocido durante el cálculo.');
        }
        state.lastResult = data;
        updateResults(data);
        updateLoadsDetail(data.loads);
        updateSummary(payload, data);
        updateInsights(data);
        if (!options.silent) {
            setFeedback('Cálculo actualizado.');
        } else {
            clearFeedback();
        }
    } catch (error) {
        console.error(error);
        setFeedback(error.message || 'No fue posible calcular la viga.', true);
    } finally {
        setLoading(false);
        state.busy = false;
    }
}

function updateResults(data) {
    elements.reactionsCards.forEach((card) => {
        const key = card.dataset.reaction;
        const reaction = data.reactions?.[key];
        const value = card.querySelector('[data-field="vertical"]');
        const meta = card.querySelector('[data-field="horizontal"]');
        if (reaction && value && meta) {
            value.textContent = `${formatNumber(reaction.vertical)} N`;
            meta.textContent = `Horizontal: ${formatNumber(reaction.horizontal)} N`;
        } else {
            if (value) value.textContent = '0.00 N';
            if (meta) meta.textContent = 'Horizontal: 0.00 N';
        }
    });

    if (data.equilibrium) {
        Object.entries(data.equilibrium).forEach(([key, value]) => {
            const el = elements.equilibrium.querySelector(`[data-field="${key}"]`);
            if (el) {
                const unit = key.includes('moment') || key === 'torsor' ? 'N·m' : 'N';
                el.textContent = `${formatNumber(value)} ${unit}`;
            }
        });
    }

    elements.centerOfMass.textContent = data.center_of_mass != null
        ? `${formatNumber(data.center_of_mass)} m`
        : '—';

    renderChart('shearChart', 'V(x)', data.diagrams?.positions, data.diagrams?.shear, palette.accent);
    renderChart('momentChart', 'M(x)', data.diagrams?.positions, data.diagrams?.moment, palette.primary);
    renderChart('torsorChart', 'T(x)', data.torsor?.positions, data.torsor?.values, palette.warning);
}

function renderChart(id, label, xValues = [], dataset = [], color) {
    if (typeof Chart === 'undefined') return;
    const ctx = document.getElementById(id);
    if (!ctx) return;

    const chart = state.charts[id];
    if (chart) {
        chart.data.labels = xValues;
        chart.data.datasets[0].data = dataset;
        chart.data.datasets[0].label = label;
        chart.data.datasets[0].borderColor = color;
        chart.data.datasets[0].backgroundColor = hexToRgba(color, 0.18);
        chart.options.scales.y.title.text = label.includes('V') ? 'F (N)' : label.includes('T') ? 'T (N·m)' : 'M (N·m)';
        chart.update();
        return;
    }

    state.charts[id] = new Chart(ctx, {
        type: 'line',
        data: {
            labels: xValues,
            datasets: [
                {
                    label,
                    data: dataset,
                    borderColor: color,
                    borderWidth: 2,
                    fill: true,
                    pointRadius: 0,
                    tension: 0.25,
                    backgroundColor: hexToRgba(color, 0.18),
                    borderCapStyle: 'round',
                },
            ],
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        label: (context) => `${label}: ${formatNumber(context.parsed.y)}`,
                    },
                },
            },
            scales: {
                x: {
                    title: { display: true, text: 'Posición (m)' },
                    ticks: { color: '#cbd5f5' },
                    grid: { color: 'rgba(148, 163, 184, 0.2)' },
                },
                y: {
                    title: { display: true, text: label.includes('V') ? 'F (N)' : label.includes('T') ? 'T (N·m)' : 'M (N·m)' },
                    ticks: { color: '#cbd5f5' },
                    grid: { color: 'rgba(148, 163, 184, 0.15)' },
                    zeroLineColor: 'rgba(148, 163, 184, 0.35)',
                },
            },
        },
    });
}

function updateLoadsDetail(loads) {
    if (!loads) return;
    const container = elements.loadsDetail;
    container.innerHTML = '';

    if (!loads.point?.length && !loads.distributed?.length) {
        container.appendChild(emptyState('Sin cargas registradas.'));
        return;
    }

    if (loads.point?.length) {
        loads.point.forEach((load, index) => {
            const row = document.createElement('div');
            row.className = 'load-row';
            row.innerHTML = `<span>CP${index + 1} · ${escapeHtml(load.label || 'Carga puntual')}</span><span>${formatNumber(load.magnitude)} N a ${formatNumber(load.position)} m</span>`;
            container.appendChild(row);
        });
    }

    if (loads.distributed?.length) {
        loads.distributed.forEach((load, index) => {
            const row = document.createElement('div');
            row.className = 'load-row';
            const title = escapeHtml(load.label || `Distribuida ${index + 1}`);
            row.innerHTML = `<span>${title}</span><span>${formatNumber(load.intensity)} N/m · ${formatNumber(load.start)}-${formatNumber(load.end)} m (F=${formatNumber(load.equivalent_force)} N)</span>`;
            container.appendChild(row);
        });
    }
}

function updateSummary(payload, result) {
    if (!elements.projectSummary) return;
    const summaryMap = {
        length: `${formatNumber(payload.length)} m`,
        'supports': `${payload.support_a_type} · ${payload.support_b_type}${payload.support_c_type && payload.support_c_type !== 'Ninguno' ? ' · ' + payload.support_c_type : ''}`,
        'point-loads': String(payload.point_loads.length),
        'distributed-loads': String(payload.distributed_loads.length),
        'center-of-mass': result.center_of_mass != null ? `${formatNumber(result.center_of_mass)} m` : '—',
        'last-run': result.metadata?.timestamp ? new Date(result.metadata.timestamp).toLocaleString('es-MX') : new Date().toLocaleString('es-MX'),
    };

    Object.entries(summaryMap).forEach(([key, value]) => {
        const el = elements.projectSummary.querySelector(`[data-summary="${key}"]`);
        if (el) {
            el.textContent = value;
        }
    });
}

function updateInsights(result) {
    if (!elements.insights) return;
    elements.insights.innerHTML = '';
    if (!result?.diagrams?.positions?.length) {
        elements.insights.appendChild(emptyListItem('Realiza un cálculo para generar insights.'));
        return;
    }

    const positions = result.diagrams.positions;
    const shear = result.diagrams.shear;
    const moment = result.diagrams.moment;

    const maxShear = maxAbsWithIndex(shear);
    const maxMoment = maxAbsWithIndex(moment);

    const insights = [
        `|V|max = ${formatNumber(maxShear.value)} N @ ${formatNumber(positions[maxShear.index] || 0)} m`,
        `|M|max = ${formatNumber(maxMoment.value)} N·m @ ${formatNumber(positions[maxMoment.index] || 0)} m`,
    ];

    if (result.reactions) {
        const ra = result.reactions.A?.vertical ?? 0;
        const rb = result.reactions.B?.vertical ?? 0;
        const rc = result.reactions.C?.vertical ?? 0;
        insights.push(`ΣReacciones = ${formatNumber(ra + rb + rc)} N`);
    }

    insights.push(`Resolución: ${result.metadata?.unit_system ?? 'SI'} · ${result.metadata?.export_format?.toUpperCase?.() || 'JSON'}`);

    insights.forEach((text) => {
        const li = document.createElement('li');
        li.textContent = text;
        elements.insights.appendChild(li);
    });
}

function resetToDefaults() {
    const defaults = deepCopy(state.defaults);
    hydrateState(defaults);
    populateForm(defaults);
    toggleSupportCField();
    renderPointLoads();
    renderDistributedLoads();
    const payload = gatherPayload();
    analyze(payload, { silent: true });
    saveState(payload);
}

function setLoading(isLoading) {
    const submit = elements.form.querySelector('button[type="submit"]');
    if (submit) {
        submit.disabled = isLoading;
        submit.textContent = isLoading ? 'Calculando…' : 'Calcular';
    }
}

function setFeedback(message, isError = false) {
    const el = elements.feedback;
    if (!el) return;
    el.textContent = message;
    el.classList.toggle('feedback--error', Boolean(isError));
}

function clearFeedback() {
    const el = elements.feedback;
    if (!el) return;
    el.textContent = '';
    el.classList.remove('feedback--error');
}

function emptyState(text) {
    const p = document.createElement('p');
    p.className = 'empty-state';
    p.textContent = text;
    return p;
}

function emptyListItem(text) {
    const li = document.createElement('li');
    li.className = 'empty-state';
    li.textContent = text;
    return li;
}

function saveState(payload) {
    try {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(payload));
    } catch (error) {
        console.warn('No se pudo guardar el estado local.', error);
    }
}

function persistAndMaybeAnalyze() {
    const payload = gatherPayload();
    saveState(payload);
    if (state.autoAnalyze) {
        analyze(payload, { silent: true });
    }
}

function loadState() {
    try {
        const raw = localStorage.getItem(STORAGE_KEY);
        return raw ? JSON.parse(raw) : null;
    } catch (error) {
        console.warn('No se pudo recuperar el estado local.', error);
        return null;
    }
}

function deepCopy(obj) {
    return JSON.parse(JSON.stringify(obj || {}));
}

function valueOr(value, fallback) {
    return value === undefined || value === null ? fallback : value;
}

function numberOr(value, fallback) {
    const num = Number(value);
    return Number.isFinite(num) ? num : fallback;
}

function formatNumber(value) {
    if (value === null || value === undefined) return '0.00';
    return Number(value).toLocaleString('es-MX', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

function cssVar(name) {
    return getComputedStyle(document.documentElement).getPropertyValue(name).trim() || '#60a5fa';
}

function hexToRgba(hex, alpha = 1) {
    const sanitized = hex.replace('#', '');
    if (sanitized.length !== 6 || Number.isNaN(parseInt(sanitized, 16))) return hex;
    const bigint = parseInt(sanitized, 16);
    const r = (bigint >> 16) & 255;
    const g = (bigint >> 8) & 255;
    const b = bigint & 255;
    return `rgba(${r}, ${g}, ${b}, ${alpha})`;
}

function escapeHtml(value) {
    return String(value)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;');
}

async function fetchTemplates(force = false) {
    if (!elements.templateList) return;
    if (!force && elements.templateList.dataset.loaded === 'true') return;

    elements.templateList.textContent = 'Cargando escenarios…';

    try {
        const response = await fetch('/api/beam/templates');
        if (!response.ok) {
            throw new Error('No se pudieron recuperar las plantillas.');
        }
        const data = await response.json();
        renderTemplates(data.categories || []);
        elements.templateList.dataset.loaded = 'true';
    } catch (error) {
        console.error(error);
        elements.templateList.textContent = 'Error al cargar las plantillas.';
    }
}

function renderTemplates(categories) {
    elements.templateList.innerHTML = '';
    if (!categories.length) {
        elements.templateList.appendChild(emptyState('No hay escenarios disponibles.'));
        return;
    }

    categories.forEach((category) => {
        const header = document.createElement('h3');
        header.textContent = category.name;
        elements.templateList.appendChild(header);

        category.items?.forEach((item) => {
            const article = document.createElement('article');
            article.className = 'template-card';
            article.innerHTML = `
                <div>
                    <p class="template-card__title">${escapeHtml(item.title)}</p>
                    <p class="template-card__description">${escapeHtml(item.description || '')}</p>
                </div>
                <button type="button" class="btn btn--ghost">Cargar</button>
            `;

            const button = article.querySelector('button');
            button.addEventListener('click', () => {
                applyTemplate(item);
            });

            elements.templateList.appendChild(article);
        });
    });
}

function applyTemplate(template) {
    const payload = template?.payload || {};
    const merged = {
        ...deepCopy(state.defaults),
        ...payload,
        point_loads: payload.point_loads || [],
        distributed_loads: payload.distributed_loads || [],
        analysis: {
            ...(state.defaults.analysis || {}),
            ...(payload.analysis || {}),
        },
    };

    hydrateState(merged);
    populateForm(merged);
    toggleSupportCField();
    renderPointLoads();
    renderDistributedLoads();
    const current = gatherPayload();
    analyze(current);
    saveState(current);
    setFeedback(`Plantilla "${template?.title || 'personalizada'}" aplicada.`);
}

function exportCurrentConfiguration() {
    const payload = gatherPayload();
    const blob = new Blob([JSON.stringify(payload, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `configuracion-viga-${Date.now()}.json`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
}

function maxAbsWithIndex(values = []) {
    let maxValue = 0;
    let index = 0;
    values.forEach((value, idx) => {
        const absValue = Math.abs(value);
        if (absValue > Math.abs(maxValue)) {
            maxValue = value;
            index = idx;
        }
    });
    return { value: maxValue, index };
}
