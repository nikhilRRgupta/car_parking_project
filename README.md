# 🚗 Smart Vehicle Parking Management System

A complete, modern, and responsive **Smart Vehicle Parking Management System** built with **Python Flask**, **MySQL 8.0**, **HTML5**, **CSS3**, **JavaScript (ES6+)**, and **Bootstrap 5.3**.

---

## 🌟 Key Features

1. **Live Parking Availability (Public / No Login Required)**
   - Real-time occupancy counters: Total Slots, Available, Occupied, and Reserved.
   - Interactive visual parking lot floor plan layout (Ground Floor, EV Bay, Basement 2-Wheeler Bay, Floor 1).
   - Auto-refreshes every 4 seconds via background AJAX polling (`/api/v1/slots/live-status`).
   - Dynamic **"PARKING FULL"** flashing alert banner when available slots reach zero.
   - Filter by vehicle category: 4-Wheeler (Cars/SUVs), 2-Wheeler (Bikes/Scooters), and EV (with Charging Station).

2. **Online Booking & Instant QR Pass**
   - Step-by-step booking wizard with visual slot selection from currently available bays.
   - Generates a unique Booking ID (`PRK-YYYYMMDD-XXXX`) and high-resolution QR Pass (`data:image/png;base64`).
   - Printable digital pass with full itinerary and customer contact details.

3. **Smart Slot Management & Anti-Double-Booking**
   - Concurrency-safe slot reservation using database row locking (`SELECT ... FOR UPDATE`).
   - 10-minute hold window for payment completion.
   - Automatic background reservation sweeper releases unpaid slots back to the available pool.
   - Slots transition to `OCCUPIED` only upon gate check-in, and return to `AVAILABLE` only after verified exit.

4. **Automated Entry Gate Management**
   - Digital scanner supports QR pass reading or manual/camera license plate input.
   - Authorizes entry only after verifying booking validity, vehicle match, and payment confirmation.
   - Realistic **Boom Barrier Simulator** with animated gate arm, traffic LED indicators (Red/Green), audio chimes, and automatic closing timer.
   - Logs every entry event with operator timestamps into the audit trail.

5. **Configurable Time-Based Pricing Engine**
   - Tiered rate calculation: e.g., ₹50 for the first 4 hours, then ₹20 for every additional started hour.
   - 15-minute grace period before charging the next hour.
   - Fully customizable rates for 4-Wheelers, 2-Wheelers, and EVs via the Admin Portal.
   - Automatically deducts pre-paid amounts when computing the final exit bill.

6. **Live Parking Timer & In-App Alerts**
   - Digital live timer on customer pass page showing countdown of the 4-hour prepaid window.
   - Automatic 30-minute reminder alert before base duration expires.
   - Real-time notification when the 4-hour base window completes and extra hourly charges begin.
   - In-app notification center and console logs simulating SMS/email dispatchers.

7. **Smart Exit Gate & Overstay Payment**
   - Scans QR pass or license plate at exit.
   - Automatically calculates total stay duration and compares with prepaid base window.
   - If exited on time: Instant authorization and barrier raise.
   - If overstay occurred: Displays itemized bill, collects remaining balance via Sandbox UPI QR or Card, verifies receipt on server, authorizes exit, and releases the parking bay.

8. **Admin Operations & Revenue Dashboard**
   - Occupancy percentage progress bar and financial KPI metrics (Today's Revenue, Total Revenue, Active Sessions).
   - Interactive **Chart.js** visualizations: 7-Day Revenue & Occupancy Trend, Vehicle Mix Doughnut.
   - Parking Slot CRUD Manager: Add bays, assign EV charging, toggle maintenance status.
   - Pricing Rules Configurator for all vehicle classes.
   - Active Stays & Overstay Monitor.
   - Complete Barrier Security Audit Trail with Emergency Manual Gate Override.

9. **Robust Database & Security**
   - Relational database schema with 9 tables (`users`, `vehicles`, `parking_slots`, `pricing_rules`, `bookings`, `parking_sessions`, `payments`, `notifications`, `barrier_audit_logs`).
   - Role-Based Access Control (`admin`, `attendant`, `customer`).
   - Werkzeug secure password hashing (PBKDF2/scrypt).
   - Parameterized SQLAlchemy queries preventing SQL injection.
   - Seamless dual database support: MySQL 8.0 primary with automatic zero-friction SQLite fallback.

---

## 📁 Project Structure

```
car_parking/
├── app/
│   ├── __init__.py                 # Flask App Factory & Blueprint registration
│   ├── config.py                   # Environment configuration & DB connection handler
│   ├── auth_utils.py               # RBAC and session decorators (@role_required)
│   ├── models/                     # SQLAlchemy Database Models
│   │   ├── __init__.py             # DB instance and model exports
│   │   ├── user.py                 # Users & Roles (Admin, Attendant, Customer)
│   │   ├── slot.py                 # Parking Slots & Zones
│   │   ├── pricing.py              # Dynamic Time-Based Pricing Rules
│   │   ├── booking.py              # Reservations & QR Tokens
│   │   ├── session.py              # Active & Completed Parking Sessions
│   │   ├── payment.py              # Financial transaction records
│   │   └── notification.py         # Notifications & Barrier Audit Logs
│   ├── services/                   # Business Logic Layer
│   │   ├── pricing_service.py      # Base pricing, overstay billing & grace calculations
│   │   ├── booking_service.py      # Concurrency locking, auto-expiry sweeper, QR generation
│   │   ├── gate_service.py         # Entry/Exit verification, barrier control, audit logging
│   │   ├── payment_service.py      # Sandbox payment gateway & UPI verification
│   │   └── notification_service.py # In-app notification dispatcher & alert logger
│   ├── routes/                     # Blueprint Modular Controllers
│   │   ├── public.py               # Public Availability, Live Layout, Pass Lookup
│   │   ├── booking.py              # Reservation wizard, Hold countdown, Sandbox Checkout
│   │   ├── gate.py                 # Entry Terminal, Exit Terminal, Barrier Simulator
│   │   ├── admin.py                # Admin Dashboard, Slot CRUD, Pricing Editor, Audit
│   │   ├── auth.py                 # Login, Registration, Session management
│   │   └── api.py                  # Live polling endpoints, Hardware webhook stubs
│   ├── static/
│   │   ├── css/
│   │   │   ├── style.css           # Modern theme styling, slot grid, digital pass
│   │   │   └── barrier.css         # Animated boom barrier, 3D arm & LED lights
│   │   └── js/
│   │       ├── live_availability.js# 4-second live slot status polling & filtering
│   │       ├── live_timer.js       # Live pass timer & 30-min/overstay alert manager
│   │       ├── gate_terminal.js    # Boom barrier audio synthesizer & cycle animation
│   │       └── admin_charts.js     # Chart.js analytics for occupancy and revenue
│   └── templates/
│       ├── base.html               # Responsive navigation, modals, flash toasts
│       ├── public/                 # Public status, Kiosk monitor, Digital Pass
│       ├── booking/                # Reservation form, Sandbox Payment checkout
│       ├── gate/                   # Entry terminal, Exit terminal, Dual simulator
│       ├── admin/                  # Dashboard, Slot manager, Pricing, Sessions, Audit
│       └── auth/                   # Sign in & Registration
├── database/
│   ├── schema.sql                  # MySQL 8.0 DDL script
│   └── seed_data.py                # Database population script (users, slots, demo data)
├── tests/
│   ├── conftest.py                 # Pytest test fixture setup
│   ├── test_pricing.py             # Unit tests for pricing engine & grace periods
│   ├── test_concurrency.py         # Tests for double-booking prevention & auto-expiry
│   └── test_gate_flow.py           # End-to-end booking -> entry -> exit -> payment test
├── .env.example                    # Environment variable template
├── .env                            # Active environment configuration
├── requirements.txt                # Python project dependencies
├── run.py                          # Application startup entry point
└── README.md                       # Comprehensive guide
```

---

## 🚀 How to Run Locally in VS Code

### 1. Open Folder in VS Code
Open VS Code, press `Ctrl + K, Ctrl + O` (or `File -> Open Folder...`) and select:
`C:\Users\NIKHIL GUPTA\Desktop\car_parking`

### 2. Open Integrated Terminal
Press ``Ctrl + ` `` (Backtick) to open the VS Code Terminal.

### 3. Verify Python & Install Dependencies
Make sure Python 3.10+ is installed:
```powershell
python --version
pip install -r requirements.txt
```

### 4. Database Setup

#### Option A: Quick Instant Run (Zero Configuration - Local SQLite)
The system is pre-configured with `ENABLE_SQLITE_FALLBACK=True` in `.env`.
It will immediately create and run on `smart_parking_local.db` without requiring any MySQL credentials!

#### Option B: Connect to MySQL 8.0 Server
1. Ensure your local MySQL service is running.
2. In MySQL, execute the schema script:
   ```powershell
   mysql -u root -p < database/schema.sql
   ```
3. Update your credentials in `.env`:
   ```ini
   DATABASE_URL=mysql+pymysql://root:YOUR_PASSWORD@localhost:3306/smart_parking_db
   ENABLE_SQLITE_FALLBACK=False
   ```

### 5. Seed Initial Data
Run the seeder script to populate default users, parking slots across multiple floors, rates, and sample bookings:
```powershell
python database/seed_data.py
```

### 6. Launch the Application
Start the Flask server:
```powershell
python run.py
```

The terminal will display:
```
=======================================================
SMART PARKING MANAGEMENT SYSTEM
=======================================================
[*] Public Portal:      http://127.0.0.1:5000
[*] Admin Portal:       http://127.0.0.1:5000/admin
[*] Entry Gate Station: http://127.0.0.1:5000/gate/entry
[*] Exit Gate Station:  http://127.0.0.1:5000/gate/exit
[*] Barrier Simulator:  http://127.0.0.1:5000/gate/barrier-simulator
=======================================================
```

Open your browser and navigate to **`http://127.0.0.1:5000`**.

---

## 🔑 Default Demo Credentials

| Role | Email | Password | Access |
| :--- | :--- | :--- | :--- |
| **System Administrator** | `admin@smartpark.com` | `admin123` | Full Admin Dashboard, Slot CRUD, Pricing Rules, Audit Logs |
| **Gate Attendant** | `attendant@smartpark.com` | `staff123` | Gate Terminals, Active Stays, Barrier Controls |
| **Customer / Driver** | `customer@example.com` | `user123` | Online Booking, Digital Pass, Live Session Timer |

---

## 🧪 Running Automated Tests

Run the test suite using `pytest`:
```powershell
python -m pytest tests -v
```

All 6 test suites verify:
- Pricing engine accuracy (4-hour base fee, overstay hourly calculations, grace period).
- Prevention of double-booking on simultaneous requests.
- Automatic release of expired unpaid slot reservations.
- End-to-end gate flow: booking -> prepayment -> gate entry -> session recording -> overstay billing -> exit gate authorization -> slot release.

---

## 💳 Payment Sandbox Details
- The payment gateway operates in Sandbox Simulation mode.
- Use the simulated **UPI QR scan** (one-click instant verification) or prefilled sandbox test card credentials.
- No real banking or card charges occur.

## 🚧 Hardware & Boom Barrier Integration Note
- Barrier movements are rendered using realistic SVG/CSS 3D animations with Web Audio chime synthesis.
- Webhook endpoints are exposed for real microcontrollers (e.g. ESP32, Arduino, Raspberry Pi):
  - `GET /api/v1/hardware/barrier/status`: Fetches gate status.
  - `POST /api/v1/hardware/barrier/ack`: Receives physical barrier switch telemetry.
- Barriers open ONLY after server-side validation of booking and payment.
