/**
 * Live Parking Availability Real-Time Polling & Visual Layout Manager
 */
document.addEventListener('DOMContentLoaded', () => {
    const totalEl = document.getElementById('count-total');
    const availEl = document.getElementById('count-available');
    const occupiedEl = document.getElementById('count-occupied');
    const reservedEl = document.getElementById('count-reserved');
    const fullBanner = document.getElementById('parking-full-banner');
    const lastUpdatedEl = document.getElementById('last-updated-time');
    const gridContainer = document.getElementById('live-slot-grid');

    // Filter controls
    const typeFilters = document.querySelectorAll('.filter-type-btn');
    const zoneFilters = document.querySelectorAll('.filter-zone-btn');

    let activeType = 'all';
    let activeZone = 'all';

    function updateLiveStatus() {
        fetch('/api/v1/slots/live-status')
            .then(res => res.json())
            .then(data => {
                if (totalEl) totalEl.textContent = data.total;
                if (availEl) availEl.textContent = data.available;
                if (occupiedEl) occupiedEl.textContent = data.occupied;
                if (reservedEl) reservedEl.textContent = data.reserved;

                // Handle Parking Full Banner
                if (fullBanner) {
                    if (data.is_full) {
                        fullBanner.classList.remove('d-none');
                    } else {
                        fullBanner.classList.add('d-none');
                    }
                }

                if (lastUpdatedEl) {
                    const now = new Date();
                    lastUpdatedEl.textContent = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
                }

                // Update individual slot cards if in DOM
                if (data.slots && data.slots.length > 0) {
                    data.slots.forEach(slot => {
                        const slotCard = document.getElementById(`slot-card-${slot.id}`);
                        if (slotCard) {
                            // Update status classes
                            slotCard.classList.remove('status-available', 'status-reserved', 'status-occupied', 'status-maintenance');
                            slotCard.classList.add(`status-${slot.status.toLowerCase()}`);

                            const statusLabel = slotCard.querySelector('.slot-status-label');
                            if (statusLabel) {
                                statusLabel.textContent = slot.status;
                            }

                            // Update selectable attribute if booking picker
                            if (slotCard.classList.contains('selectable')) {
                                if (slot.status !== 'AVAILABLE') {
                                    slotCard.classList.remove('selectable');
                                    slotCard.style.pointerEvents = 'none';
                                } else {
                                    slotCard.classList.add('selectable');
                                    slotCard.style.pointerEvents = 'auto';
                                }
                            }
                        }
                    });
                }
            })
            .catch(err => console.debug('Live polling standby:', err));
    }

    // Filter by vehicle type
    typeFilters.forEach(btn => {
        btn.addEventListener('click', () => {
            typeFilters.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            activeType = btn.getAttribute('data-type');
            applyFilters();
        });
    });

    // Filter by floor zone
    zoneFilters.forEach(btn => {
        btn.addEventListener('click', () => {
            zoneFilters.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            activeZone = btn.getAttribute('data-zone');
            applyFilters();
        });
    });

    function applyFilters() {
        const slotBoxes = document.querySelectorAll('.slot-box');
        slotBoxes.forEach(box => {
            const vType = box.getAttribute('data-vehicle-type');
            const zone = box.getAttribute('data-floor-zone');
            const isEv = box.getAttribute('data-is-ev') === 'true';

            let typeMatch = (activeType === 'all');
            if (activeType === 'ev') typeMatch = isEv;
            else if (activeType !== 'all') typeMatch = (vType === activeType);

            let zoneMatch = (activeZone === 'all' || zone === activeZone);

            if (typeMatch && zoneMatch) {
                box.style.display = 'block';
            } else {
                box.style.display = 'none';
            }
        });
    }

    // Initial run and poll every 4 seconds
    updateLiveStatus();
    setInterval(updateLiveStatus, 4000);
});
