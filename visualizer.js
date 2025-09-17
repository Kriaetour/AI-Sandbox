// visualizer.js - AI Sandbox World Viewer

const canvas = document.getElementById('worldCanvas');
const ctx = canvas.getContext('2d');
const TILE_SIZE = 20; // Size of each tile in pixels
const CHUNK_SIZE = 16; // Assuming 16x16 chunks (typical)
let AUTO_CENTER = true; // Becomes false once user pans/zooms; press 'C' to restore

// Camera state
let camera = { offsetX: 0, offsetY: 0, scale: 1 };
const MIN_SCALE = 0.3;
const MAX_SCALE = 3.5;
const ZOOM_IN_FACTOR = 1.1;
const ZOOM_OUT_FACTOR = 0.9;
const PAN_STEP = 40; // pixels per key press (screen space)
let userAdjusted = false;

// Minimap references (added to index.html)
const minimap = document.getElementById('minimap');
const mctx = minimap ? minimap.getContext('2d') : null;

function applyZoom(factor, focusX, focusY) {
    const oldScale = camera.scale;
    const newScale = Math.min(MAX_SCALE, Math.max(MIN_SCALE, oldScale * factor));
    if (newScale === oldScale) return;
    // World coords of focus point before zoom
    const worldX = (focusX - camera.offsetX) / oldScale;
    const worldY = (focusY - camera.offsetY) / oldScale;
    camera.scale = newScale;
    // Adjust offset so the focus point stays under cursor
    camera.offsetX = focusX - worldX * newScale;
    camera.offsetY = focusY - worldY * newScale;
}

window.addEventListener('wheel', e => {
    if (!canvas.contains(e.target)) return;
    e.preventDefault();
    AUTO_CENTER = false; userAdjusted = true;
    const factor = e.deltaY < 0 ? ZOOM_IN_FACTOR : ZOOM_OUT_FACTOR;
    applyZoom(factor, e.offsetX, e.offsetY);
});

window.addEventListener('keydown', e => {
    const key = e.key.toLowerCase();
    let moved = false;
    if (['w', 'arrowup'].includes(key)) { camera.offsetY += PAN_STEP; moved = true; }
    if (['s', 'arrowdown'].includes(key)) { camera.offsetY -= PAN_STEP; moved = true; }
    if (['a', 'arrowleft'].includes(key)) { camera.offsetX += PAN_STEP; moved = true; }
    if (['d', 'arrowright'].includes(key)) { camera.offsetX -= PAN_STEP; moved = true; }
    if (key === 'c') { AUTO_CENTER = true; userAdjusted = false; }
    if (moved) { AUTO_CENTER = false; userAdjusted = true; }
});

// Mouse drag panning
let isDragging = false;
let dragStart = { x: 0, y: 0 };
let dragCameraStart = { x: 0, y: 0 };

canvas.addEventListener('mousedown', e => {
    isDragging = true;
    dragStart.x = e.clientX;
    dragStart.y = e.clientY;
    dragCameraStart.x = camera.offsetX;
    dragCameraStart.y = camera.offsetY;
});

window.addEventListener('mousemove', e => {
    if (!isDragging) return;
    const dx = e.clientX - dragStart.x;
    const dy = e.clientY - dragStart.y;
    camera.offsetX = dragCameraStart.x + dx;
    camera.offsetY = dragCameraStart.y + dy;
    AUTO_CENTER = false; userAdjusted = true;
});

window.addEventListener('mouseup', () => { isDragging = false; });
window.addEventListener('mouseleave', () => { isDragging = false; });

// Define colors for all 20 biomes
const BIOME_COLORS = {
    'PLAINS': '#8db360',
    'FOREST': '#3a7d44',
    'MOUNTAINS': '#a1a1a1',
    'DESERT': '#c2b280',
    'WATER': '#4d7c9e',
    'SWAMP': '#5d6b47',
    'TUNDRA': '#e8e8e8',
    'JUNGLE': '#2d5016',
    'HILLS': '#7a8c69',
    'VALLEY': '#90a955',
    'CANYON': '#8b7355',
    'COASTAL': '#87ceeb',
    'ISLAND': '#98fb98',
    'VOLCANIC': '#2f1b14',
    'SAVANNA': '#d2b48c',
    'TAIGA': '#4682b4',
    'STEPPE': '#deb887',
    'BADLANDS': '#8b4513',
    'GLACIER': '#f0f8ff',
    'OASIS': '#00ced1'
};

// Faction colors for NPCs
const FACTION_COLORS = [
    '#ff4444', '#44ff44', '#4444ff', '#ffff44', '#ff44ff', '#44ffff',
    '#ff8844', '#88ff44', '#4488ff', '#ff4488', '#88ff88', '#8844ff'
];

let lastData = null;
let factionColorMap = new Map();

// Create biome legend
function createBiomeLegend() {
    const legendContainer = document.getElementById('biomeLegend');
    Object.entries(BIOME_COLORS).forEach(([biome, color]) => {
        const legendItem = document.createElement('div');
        legendItem.className = 'legend-item';

        const colorBox = document.createElement('div');
        colorBox.className = 'legend-color';
        colorBox.style.backgroundColor = color;

        const label = document.createTextNode(biome.toLowerCase());

        legendItem.appendChild(colorBox);
        legendItem.appendChild(label);
        legendContainer.appendChild(legendItem);
    });
}

let consecutiveFailures = 0;
let lastHealth = null;
const STALE_THRESHOLD_SECONDS = 3; // consider data stale if no update in this window

async function fetchWorldState() {
    try {
        const [healthResp, stateResp] = await Promise.all([
            fetch('http://127.0.0.1:5000/health', { cache: 'no-store' }),
            fetch('http://127.0.0.1:5000/world_state', { cache: 'no-store' })
        ]);

        if (healthResp.ok) {
            lastHealth = await healthResp.json();
        }

        if (!stateResp.ok) {
            throw new Error(`World state HTTP ${stateResp.status}`);
        }
        const data = await stateResp.json();

        consecutiveFailures = 0;

        // Determine freshness
        const now = Date.now() / 1000;
        const age = (data.last_updated ? (now - data.last_updated) : null);
        const stale = age !== null && age > STALE_THRESHOLD_SECONDS;

        const statusEl = document.getElementById('connectionStatus');
        statusEl.className = 'status connected';
        statusEl.textContent = stale ? `Connected (stale ${age.toFixed(1)}s)` : 'Connected';

        // Update stats
        document.getElementById('tick').textContent = data.tick ?? 0;
        document.getElementById('season').textContent = data.season ?? 'Unknown';
        document.getElementById('population').textContent = data.population ?? 0;
        document.getElementById('food').textContent = (data.total_food ?? 0).toFixed(1);
        document.getElementById('chunks').textContent = data.chunks?.length ?? 0;
        document.getElementById('factions').textContent = data.factions?.length ?? 0;

        lastData = data;
        drawWorld(data);
    } catch (err) {
        consecutiveFailures += 1;
        console.error('Fetch failure', err, 'count=', consecutiveFailures);

        // Only flip to disconnected after a few consecutive failures to avoid flicker
        if (consecutiveFailures >= 3) {
            const statusEl = document.getElementById('connectionStatus');
            statusEl.className = 'status disconnected';
            statusEl.textContent = 'Disconnected - ensure API running: python run_api_server.py';
        }

        if (lastData) {
            drawWorld(lastData);
        } else if (consecutiveFailures >= 3) {
            drawDemoData();
        }
    }
}

function drawWorld(data) {
    // Clear the canvas
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // Compute bounds of chunks or NPCs for auto-centering
    if (AUTO_CENTER) {
        let xs = [], ys = [];
        if (data.chunks && data.chunks.length) {
            data.chunks.forEach(ch => { xs.push(ch.coordinates[0]); ys.push(ch.coordinates[1]); });
        } else if (data.npcs && data.npcs.length) {
            data.npcs.forEach(n => { xs.push(n.coordinates[0]/CHUNK_SIZE); ys.push(n.coordinates[1]/CHUNK_SIZE); });
        }
        if (xs.length) {
            const minX = Math.min(...xs), maxX = Math.max(...xs);
            const minY = Math.min(...ys), maxY = Math.max(...ys);
            const worldPixelWidth = (maxX - minX + 1) * CHUNK_SIZE * TILE_SIZE;
            const worldPixelHeight = (maxY - minY + 1) * CHUNK_SIZE * TILE_SIZE;
            // Center offsets (ensure central tile appears middle)
            const centerX = (minX + maxX + 1) / 2 * CHUNK_SIZE * TILE_SIZE;
            const centerY = (minY + maxY + 1) / 2 * CHUNK_SIZE * TILE_SIZE;
            camera.offsetX = canvas.width / 2 - centerX * camera.scale;
            camera.offsetY = canvas.height / 2 - centerY * camera.scale;
        }
    }

    // Draw chunks
    data.chunks?.forEach(chunk => { drawChunk(chunk); });

    // Determine if all NPCs stacked (same coordinate)
    let stacked = false;
    if (data.npcs && data.npcs.length > 1) {
        const first = JSON.stringify(data.npcs[0].coordinates);
        stacked = data.npcs.every(n => JSON.stringify(n.coordinates) === first);
    }
    data.npcs?.forEach(npc => drawNPC(npc, data.factions, stacked));

    // Draw faction territories (if available)
    data.factions?.forEach(faction => { drawFactionTerritory(faction); });

    drawMinimap(data);
}

function drawChunk(chunk) {
    const chunkX = chunk.coordinates[0];
    const chunkY = chunk.coordinates[1];
    const terrain = chunk.terrain;

    // Draw chunk background
    const color = BIOME_COLORS[terrain] || BIOME_COLORS['PLAINS'];
    ctx.fillStyle = color;
    const baseX = chunkX * CHUNK_SIZE * TILE_SIZE;
    const baseY = chunkY * CHUNK_SIZE * TILE_SIZE;
    const dim = CHUNK_SIZE * TILE_SIZE * camera.scale;
    ctx.fillRect(
        baseX * camera.scale + camera.offsetX,
        baseY * camera.scale + camera.offsetY,
        dim,
        dim
    );

    // Draw chunk border
    ctx.strokeStyle = '#333';
    ctx.lineWidth = 1;
    ctx.strokeRect(
        baseX * camera.scale + camera.offsetX,
        baseY * camera.scale + camera.offsetY,
        dim,
        dim
    );

    // Draw settlement indicators
    if (chunk.is_settlement) {
        ctx.fillStyle = '#ffff00';
        ctx.beginPath();
        ctx.arc(
            (chunkX * CHUNK_SIZE + CHUNK_SIZE/2) * TILE_SIZE * camera.scale + camera.offsetX,
            (chunkY * CHUNK_SIZE + CHUNK_SIZE/2) * TILE_SIZE * camera.scale + camera.offsetY,
            TILE_SIZE * 2 * camera.scale,
            0, 2 * Math.PI
        );
        ctx.fill();
    }

    // Draw castle indicators
    if (chunk.is_castle) {
        ctx.fillStyle = '#ff0000';
        ctx.fillRect(
            (chunkX * CHUNK_SIZE + CHUNK_SIZE/2 - 0.5) * TILE_SIZE * camera.scale + camera.offsetX,
            (chunkY * CHUNK_SIZE + CHUNK_SIZE/2 - 0.5) * TILE_SIZE * camera.scale + camera.offsetY,
            TILE_SIZE * camera.scale,
            TILE_SIZE * camera.scale
        );
    }
}

function drawNPC(npc, factions, stacked) {
    const [x, y] = npc.coordinates;

    // Jitter to separate overlapping NPCs visually when all share same tile
    let jitterX = 0, jitterY = 0;
    if (stacked) {
        const jitterScale = TILE_SIZE * 0.3;
        jitterX = (Math.random() - 0.5) * jitterScale;
        jitterY = (Math.random() - 0.5) * jitterScale;
    }

    // Get faction color
    let factionColor = '#ffffff'; // Default white
    if (npc.faction_id) {
        if (!factionColorMap.has(npc.faction_id)) {
            const factionIndex = factions?.findIndex(f => f.name === npc.faction_id) || 0;
            factionColorMap.set(npc.faction_id, FACTION_COLORS[factionIndex % FACTION_COLORS.length]);
        }
        factionColor = factionColorMap.get(npc.faction_id);
    }

    // Draw NPC as circle
    ctx.fillStyle = factionColor;
    ctx.beginPath();
    ctx.arc(
        (x + 0.5) * TILE_SIZE * camera.scale + (jitterX) * camera.scale + camera.offsetX,
        (y + 0.5) * TILE_SIZE * camera.scale + (jitterY) * camera.scale + camera.offsetY,
        (TILE_SIZE / 3) * camera.scale,
        0, 2 * Math.PI
    );
    ctx.fill();

    // Draw ambition indicator (small dot)
    if (npc.ambition_type) {
        ctx.fillStyle = '#ffff00';
        ctx.beginPath();
        ctx.arc(
            (x + 0.5) * TILE_SIZE * camera.scale + (jitterX) * camera.scale + camera.offsetX,
            (y + 0.5) * TILE_SIZE * camera.scale + (jitterY) * camera.scale + camera.offsetY,
            (TILE_SIZE / 6) * camera.scale,
            0, 2 * Math.PI
        );
        ctx.fill();
    }
}

function drawMinimap(data) {
    if (!mctx) return;
    mctx.clearRect(0, 0, minimap.width, minimap.height);
    const padding = 4;
    const chunks = data.chunks || [];
    if (!chunks.length) return;
    const xs = chunks.map(c => c.coordinates[0]);
    const ys = chunks.map(c => c.coordinates[1]);
    const minX = Math.min(...xs), maxX = Math.max(...xs);
    const minY = Math.min(...ys), maxY = Math.max(...ys);
    const spanX = maxX - minX + 1;
    const spanY = maxY - minY + 1;
    const scale = Math.min((minimap.width - padding * 2) / spanX, (minimap.height - padding * 2) / spanY);
    // Draw chunks
    chunks.forEach(ch => {
        const mx = (ch.coordinates[0] - minX) * scale + padding;
        const my = (ch.coordinates[1] - minY) * scale + padding;
        mctx.fillStyle = BIOME_COLORS[ch.terrain] || '#555';
        mctx.fillRect(mx, my, scale, scale);
    });
    // Draw NPCs
    if (data.npcs) {
        data.npcs.forEach(n => {
            const cx = (Math.floor(n.coordinates[0]/CHUNK_SIZE) - minX + 0.5) * scale + padding;
            const cy = (Math.floor(n.coordinates[1]/CHUNK_SIZE) - minY + 0.5) * scale + padding;
            mctx.fillStyle = '#ffffff';
            mctx.beginPath();
            mctx.arc(cx, cy, Math.max(2, scale * 0.2), 0, 2 * Math.PI);
            mctx.fill();
        });
    }
    // Camera viewport rectangle (approximate)
    const worldChunkWidth = canvas.width / (CHUNK_SIZE * TILE_SIZE * camera.scale);
    const worldChunkHeight = canvas.height / (CHUNK_SIZE * TILE_SIZE * camera.scale);
    const topLeftWorldX = (-camera.offsetX) / (CHUNK_SIZE * TILE_SIZE * camera.scale);
    const topLeftWorldY = (-camera.offsetY) / (CHUNK_SIZE * TILE_SIZE * camera.scale);
    mctx.strokeStyle = '#ffffff';
    mctx.lineWidth = 1;
    mctx.strokeRect(
        (topLeftWorldX - minX) * scale + padding,
        (topLeftWorldY - minY) * scale + padding,
        worldChunkWidth * scale,
        worldChunkHeight * scale
    );
}

function drawDemoData() {
    // Create some demo data to show when API is not connected
    const demoData = {
        tick: 0,
        season: 'Demo',
        population: 5,
        total_food: 100.0,
        npcs: [
            {id: 1, name: 'DemoNPC1', coordinates: [5, 5], faction_id: 'DemoFaction1', health: 100, age: 25},
            {id: 2, name: 'DemoNPC2', coordinates: [10, 10], faction_id: 'DemoFaction2', health: 90, age: 30},
            {id: 3, name: 'DemoNPC3', coordinates: [15, 5], faction_id: 'DemoFaction1', health: 80, age: 20}
        ],
        factions: [
            {name: 'DemoFaction1', population: 2, resources: {food: 50.0}},
            {name: 'DemoFaction2', population: 1, resources: {food: 30.0}}
        ],
        chunks: [
            {coordinates: [0, 0], terrain: 'PLAINS', is_active: true},
            {coordinates: [1, 0], terrain: 'FOREST', is_active: true},
            {coordinates: [0, 1], terrain: 'WATER', is_active: true},
            {coordinates: [1, 1], terrain: 'MOUNTAINS', is_active: true}
        ]
    };

    // Update stats with demo data
    document.getElementById('tick').textContent = demoData.tick;
    document.getElementById('season').textContent = demoData.season;
    document.getElementById('population').textContent = demoData.population;
    document.getElementById('food').textContent = demoData.total_food.toFixed(1);
    document.getElementById('chunks').textContent = demoData.chunks.length;
    document.getElementById('factions').textContent = demoData.factions.length;

    drawWorld(demoData);
}

// Initialize
createBiomeLegend();

// Start the render loop
setInterval(fetchWorldState, 1000); // Update every second

// Initial fetch
fetchWorldState();