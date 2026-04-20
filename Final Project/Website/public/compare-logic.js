// Handles shared compare functionality across all pages
const DEFAULT_IMAGE = 'https://images.unsplash.com/photo-1549317661-bd32c8ce0db2?auto=format&fit=crop&q=80&w=800';

window.compareList = JSON.parse(localStorage.getItem('compareList') || '[]');

function getCompareList() {
    return window.compareList;
}

function notifyCompareUpdated() {
    window.dispatchEvent(new CustomEvent('3arabeetak:compare-updated', {
        detail: { compareList: getCompareList().slice() }
    }));
}

window.addEventListener('storage', (e) => {
    if (e.key !== 'compareList') return;
    window.compareList = JSON.parse(localStorage.getItem('compareList') || '[]');
    renderCompareBar();
    notifyCompareUpdated();
});

document.addEventListener('DOMContentLoaded', () => {
    injectCompareBar();
    renderCompareBar();
});

function injectCompareBar() {
    const bar = document.createElement('div');
    bar.id = 'compare-bar';
    bar.className = 'compare-bar hidden';
    bar.innerHTML = `
        <div class="compare-bar-content">
            <div class="compare-slots" id="compare-slots">
                <!-- Selected cars go here -->
            </div>
            <div class="compare-actions">
                <button class="btn-compare-primary" onclick="goToCompare()" id="btn-compare-now" disabled>Compare <span id="compare-count">(0/3)</span></button>
                <button class="btn-compare-secondary" onclick="clearComparison()">Clear</button>
            </div>
        </div>
    `;
    document.body.appendChild(bar);
}

function saveCompareList() {
    localStorage.setItem('compareList', JSON.stringify(getCompareList()));
    notifyCompareUpdated();
}

/**
 * Parses the image_paths value from the database.
 * Handles multiple formats:
 *   - Semicolon-separated local paths: "Used_Images\\folder\\img.jpg; Used_Images\\folder\\img2.jpg"
 *   - JSON arrays: "['url1', 'url2']"
 *   - Comma-separated URLs: "http://..., http://..."
 *   - Single path/URL
 * Returns an array of web-servable URLs (prepends / for local paths).
 */
function parseImagesLogic(imagePathsStr) {
    if (!imagePathsStr) return [];

    // Check if it's semicolon-separated local paths (our primary format)
    if (imagePathsStr.includes(';')) {
        return imagePathsStr.split(';')
            .map(p => p.trim())
            .filter(p => p.length > 0)
            .map(p => {
                // Convert backslashes to forward slashes
                let cleaned = p.replace(/\\/g, '/').replace(/['"[\]]/g, '');
                // Prepend / if it's a local path (not starting with http)
                if (!cleaned.startsWith('http') && !cleaned.startsWith('/')) {
                    cleaned = '/' + cleaned;
                }
                return cleaned;
            });
    }

    // Try JSON array format (legacy)
    try {
        const cleanedStr = imagePathsStr.replace(/'/g, '"');
        const urls = JSON.parse(cleanedStr);
        if (Array.isArray(urls)) {
            return urls.filter(u => u && u.trim().length > 0).map(u => {
                let cleaned = u.trim().replace(/\\/g, '/');
                if (!cleaned.startsWith('http') && !cleaned.startsWith('/')) {
                    cleaned = '/' + cleaned;
                }
                return cleaned;
            });
        }
        return [urls];
    } catch(e) {
        // Comma-separated or single value
        if (imagePathsStr.startsWith('http')) return [imagePathsStr];
        const splitUrls = imagePathsStr.split(',');
        if (splitUrls.length > 0) {
            return splitUrls.map(u => {
                let cleaned = u.trim().replace(/['"[\]]/g, '').replace(/\\/g, '/');
                if (!cleaned.startsWith('http') && !cleaned.startsWith('/')) {
                    cleaned = '/' + cleaned;
                }
                return cleaned;
            }).filter(u => u.length > 1);
        }
        return [];
    }
}

window.toggleCompare = function(e, id, name, img) {
    if (e) {
        e.stopPropagation();
        e.preventDefault();
    }
    
    id = String(id);
    const compareList = getCompareList();
    const existingIndex = compareList.findIndex(c => String(c.id) === id);
    let isNowAdded = false;
    
    if (existingIndex >= 0) {
        compareList.splice(existingIndex, 1);
        isNowAdded = false;
    } else {
        if (compareList.length >= 3) {
            alert('You can only compare up to 3 cars at a time.');
            return;
        }
        compareList.push({ id, name, img });
        isNowAdded = true;
    }
    
    saveCompareList();
    
    // Update any icons on the current page
    const gridBtns = document.querySelectorAll(`.btn-compare-icon[data-car-id="${id}"]`);
    gridBtns.forEach(btn => {
        if (isNowAdded) {
            btn.classList.add('bg-emerald-500', 'text-white', 'border-emerald-500');
            btn.classList.remove('bg-white/10', 'text-gray-300', 'border-transparent', 'bg-white/90', 'text-gray-700');
            btn.innerHTML = '<i class="fa-solid fa-check mr-1"></i> Added';
        } else {
            btn.classList.remove('bg-emerald-500', 'text-white', 'border-emerald-500');
            btn.classList.add('bg-white/10', 'text-gray-300', 'border-transparent');
            btn.innerHTML = '<i class="fa-solid fa-plus mr-1"></i> Compare';
        }
    });

    // Update detail button if on car detail page
    const detailBtn = document.getElementById('detail-btn-compare');
    if (detailBtn && detailBtn.getAttribute('data-car-id') == id) {
        if (isNowAdded) {
            detailBtn.classList.add('bg-emerald-500', 'hover:bg-emerald-600');
            detailBtn.classList.remove('bg-blue-600', 'hover:bg-blue-700');
            detailBtn.innerHTML = '<i class="fa-solid fa-check mr-2"></i> Added to Compare';
        } else {
            detailBtn.classList.remove('bg-emerald-500', 'hover:bg-emerald-600');
            detailBtn.classList.add('bg-blue-600', 'hover:bg-blue-700');
            detailBtn.innerHTML = '<i class="fa-solid fa-plus mr-2"></i> Add to Compare';
        }
    }
    
    renderCompareBar();
    return isNowAdded;
};

window.renderCompareBar = function() {
    const bar = document.getElementById('compare-bar');
    if (!bar) return;
    
    const slots = document.getElementById('compare-slots');
    const count = document.getElementById('compare-count');
    const btnCompare = document.getElementById('btn-compare-now');
    
    const compareList = getCompareList();

    if (compareList.length === 0) {
        bar.classList.add('hidden');
        return;
    }
    
    bar.classList.remove('hidden');
    count.innerText = `(${compareList.length}/3)`;
    btnCompare.disabled = compareList.length < 2;

    slots.innerHTML = '';
    compareList.forEach(car => {
        slots.innerHTML += `
            <div class="compare-slot">
                <img src="${car.img}" alt="${car.name}" onerror="this.src='${DEFAULT_IMAGE}'">
                <div class="compare-slot-info">
                    <span class="compare-slot-name" title="${car.name}">${car.name}</span>
                </div>
                <button class="btn-remove-slot" onclick="toggleCompare(event, '${car.id}', '', '')">
                    <i class="fa-solid fa-xmark text-xs"></i>
                </button>
            </div>
        `;
    });
};

window.clearComparison = function() {
    window.compareList = [];
    saveCompareList();
    renderCompareBar();
    
    // Reset all grid buttons
    document.querySelectorAll('.btn-compare-icon').forEach(btn => {
        btn.classList.remove('bg-emerald-500', 'text-white', 'border-emerald-500', 'bg-blue-600', 'border-blue-600');
        btn.classList.add('bg-white/10', 'text-gray-300', 'border-transparent');
        btn.innerHTML = '<i class="fa-solid fa-plus mr-1"></i> Compare';
    });
    
    // Reset detail button if present
    const detailBtn = document.getElementById('detail-btn-compare');
    if (detailBtn) {
        detailBtn.classList.remove('bg-emerald-500', 'hover:bg-emerald-600');
        detailBtn.classList.add('bg-blue-600', 'hover:bg-blue-700');
        detailBtn.innerHTML = '<i class="fa-solid fa-plus mr-2"></i> Add to Compare';
    }
};

window.goToCompare = function() {
    const compareList = getCompareList();
    if (compareList.length < 2) return;
    window.location.href = '/compare';
};
