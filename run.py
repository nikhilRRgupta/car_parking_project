import os
from app import create_app
from database.seed_data import seed_database

app = create_app()

if __name__ == '__main__':
    # Auto-seed initial demo data if database is empty
    with app.app_context():
        from app.models import ParkingSlot
        if ParkingSlot.query.count() == 0:
            print("[*] Database empty. Auto-seeding initial slots and configuration...")
            seed_database()

    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('DEBUG', 'True').lower() in ('true', '1', 'yes')
    print("\n=======================================================")
    print("SMART PARKING MANAGEMENT SYSTEM")
    print("=======================================================")
    print(f"[*] Public Portal:      http://127.0.0.1:{port}")
    print(f"[*] Admin Portal:       http://127.0.0.1:{port}/admin")
    print(f"[*] Entry Gate Station: http://127.0.0.1:{port}/gate/entry")
    print(f"[*] Exit Gate Station:  http://127.0.0.1:{port}/gate/exit")
    print(f"[*] Barrier Simulator:  http://127.0.0.1:{port}/gate/barrier-simulator")
    print("=======================================================\n")
    app.run(host='0.0.0.0', port=port, debug=debug)
