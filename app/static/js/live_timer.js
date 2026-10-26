/**
 * Live Parking Session Timer & Overstay Alert Manager
 */
document.addEventListener('DOMContentLoaded', () => {
    const timerContainer = document.getElementById('session-timer-container');
    if (!timerContainer) return;

    const bookingCode = timerContainer.getAttribute('data-booking-code');
    const timerDigits = document.getElementById('timer-digits');
    const timerSubtext = document.getElementById('timer-subtext');
    const currentBillEl = document.getElementById('live-current-bill');
    const alertBox = document.getElementById('timer-alert-box');

    let notified30Min = false;
    let notifiedOvertime = false;

    function formatTime(totalSeconds) {
        const hrs = Math.floor(totalSeconds / 3600);
        const mins = Math.floor((totalSeconds % 3600) / 60);
        const secs = totalSeconds % 60;
        return `${String(hrs).padStart(2, '0')}:${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;
    }

    function pollTimer() {
        fetch(`/api/v1/session/timer/${bookingCode}`)
            .then(res => res.json())
            .then(data => {
                if (!data.is_active) {
                    if (data.status === 'COMPLETED') {
                        timerDigits.textContent = 'SESSION COMPLETED';
                        timerDigits.className = 'timer-digits text-secondary';
                        timerSubtext.textContent = `Total Stay: ${data.total_duration_minutes} mins | Final Bill: ₹${data.total_amount.toFixed(2)}`;
                    } else {
                        timerDigits.textContent = 'AWAITING ENTRY';
                        timerDigits.className = 'timer-digits text-muted';
                        timerSubtext.textContent = 'Timer will start as soon as your vehicle enters through the gate.';
                    }
                    return;
                }

                // Active Session
                const elapsedSec = data.elapsed_seconds;
                const baseSec = data.base_minutes * 60;

                if (elapsedSec < baseSec) {
                    // Normal within prepaid base duration
                    const remainingSec = baseSec - elapsedSec;
                    timerDigits.textContent = formatTime(remainingSec);
                    timerDigits.className = 'timer-digits timer-normal';
                    timerSubtext.textContent = `Remaining in Prepaid Base Window (${data.base_hours} hrs)`;

                    // 30-minute warning check
                    if (data.is_30min_warning) {
                        timerDigits.className = 'timer-digits timer-warning';
                        if (alertBox) {
                            alertBox.className = 'alert alert-warning mt-3';
                            alertBox.innerHTML = '<i class="fas fa-hourglass-half me-2"></i><strong>Reminder:</strong> Less than 30 minutes remaining in your prepaid base window.';
                            alertBox.classList.remove('d-none');
                        }
                    }
                } else {
                    // Overtime window
                    const overstaySec = elapsedSec - baseSec;
                    timerDigits.textContent = `+${formatTime(overstaySec)}`;
                    timerDigits.className = 'timer-digits timer-overtime';
                    timerSubtext.innerHTML = `<span class="badge bg-danger">OVERTIME ACTIVE</span> Additional ₹${data.hourly_rate.toFixed(2)}/hr started`;

                    if (alertBox) {
                        alertBox.className = 'alert alert-danger mt-3';
                        alertBox.innerHTML = `<i class="fas fa-exclamation-triangle me-2"></i><strong>Notice:</strong> 4-hour base window completed! Additional overstay charge is ₹${data.extra_charge.toFixed(2)} (Payable at exit).`;
                        alertBox.classList.remove('d-none');
                    }
                }

                if (currentBillEl) {
                    currentBillEl.textContent = `₹${data.gross_amount.toFixed(2)}`;
                }
            })
            .catch(err => console.debug('Timer poll standby:', err));
    }

    pollTimer();
    setInterval(pollTimer, 2000);
});
