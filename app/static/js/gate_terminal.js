/**
 * Gate Terminal & Animated Boom Barrier Audio-Visual Controller
 */

class BarrierAudioSynth {
    constructor() {
        this.ctx = null;
    }

    init() {
        if (!this.ctx) {
            const AudioContext = window.AudioContext || window.webkitAudioContext;
            if (AudioContext) {
                this.ctx = new AudioContext();
            }
        }
    }

    playSuccessChime() {
        try {
            this.init();
            if (!this.ctx) return;
            const now = this.ctx.currentTime;
            const osc = this.ctx.createOscillator();
            const gain = this.ctx.createGain();

            osc.type = 'sine';
            osc.frequency.setValueAtTime(587.33, now); // D5
            osc.frequency.exponentialRampToValueAtTime(880, now + 0.15); // A5
            gain.gain.setValueAtTime(0.3, now);
            gain.gain.exponentialRampToValueAtTime(0.01, now + 0.4);

            osc.connect(gain);
            gain.connect(this.ctx.destination);
            osc.start(now);
            osc.stop(now + 0.4);
        } catch (e) {
            console.debug('Audio synth fallback', e);
        }
    }

    playDenyBuzzer() {
        try {
            this.init();
            if (!this.ctx) return;
            const now = this.ctx.currentTime;
            const osc = this.ctx.createOscillator();
            const gain = this.ctx.createGain();

            osc.type = 'sawtooth';
            osc.frequency.setValueAtTime(160, now);
            gain.gain.setValueAtTime(0.3, now);
            gain.gain.exponentialRampToValueAtTime(0.01, now + 0.35);

            osc.connect(gain);
            gain.connect(this.ctx.destination);
            osc.start(now);
            osc.stop(now + 0.35);
        } catch (e) {
            console.debug('Audio synth fallback', e);
        }
    }
}

const barrierAudio = new BarrierAudioSynth();

/**
 * Executes realistic boom barrier cycle:
 * 1. Switch LED: Red -> Green
 * 2. Play Audio chime
 * 3. Rotate arm (-75 deg)
 * 4. Move simulated car through gate
 * 5. Wait auto-close seconds (e.g. 5s)
 * 6. Lower arm (0 deg)
 * 7. Switch LED: Green -> Red
 */
function animateBarrierGate(barrierWrapperId, autoCloseSeconds = 5) {
    const wrapper = document.getElementById(barrierWrapperId);
    if (!wrapper) return;

    const barrierSys = wrapper.querySelector('.barrier-system');
    const redLed = wrapper.querySelector('.traffic-led.red');
    const greenLed = wrapper.querySelector('.traffic-led.green');
    const statusBadge = wrapper.querySelector('.barrier-status-badge');
    const vehicle = wrapper.querySelector('.sim-vehicle');

    barrierAudio.playSuccessChime();

    // 1. Open
    if (redLed) redLed.classList.remove('active');
    if (greenLed) greenLed.classList.add('active');
    if (barrierSys) barrierSys.classList.add('open');
    if (statusBadge) {
        statusBadge.className = 'barrier-status-badge badge-open';
        statusBadge.innerHTML = '<i class="fas fa-arrow-up"></i> BARRIER RAISED (OPEN)';
    }

    // Pass vehicle through
    if (vehicle) {
        setTimeout(() => {
            vehicle.classList.add('passing');
        }, 800);
    }

    // 2. Auto-close cycle
    setTimeout(() => {
        if (barrierSys) barrierSys.classList.remove('open');
        if (greenLed) greenLed.classList.remove('active');
        if (redLed) redLed.classList.add('active');
        if (statusBadge) {
            statusBadge.className = 'barrier-status-badge badge-closed';
            statusBadge.innerHTML = '<i class="fas fa-lock"></i> BARRIER CLOSED';
        }
        if (vehicle) {
            setTimeout(() => {
                vehicle.classList.remove('passing');
            }, 1200);
        }
    }, autoCloseSeconds * 1000);
}

// Auto-trigger if server returned barrier_action == 'OPEN'
document.addEventListener('DOMContentLoaded', () => {
    const triggerData = document.getElementById('auto-barrier-trigger');
    if (triggerData && triggerData.getAttribute('data-action') === 'OPEN') {
        const wrapperId = triggerData.getAttribute('data-target') || 'entry-barrier-visualizer';
        setTimeout(() => {
            animateBarrierGate(wrapperId);
        }, 300);
    }
});
