import threading
import time
from sqlalchemy import text
from app.db.session import SessionLocal

def thread_a_proper_order():
    db = SessionLocal()
    try:
        print("[Thread A] 🟢 Started. Attempting to lock Account 1...")
        db.execute(text("SELECT * FROM accounts WHERE id = 1 FOR UPDATE;"))
        print("[Thread A] 🔒 Account 1 locked. Doing some work...")
        
        time.sleep(2) # Simulating Python processing time
        
        print("[Thread A] ⏳ Attempting to lock Holding AAPL...")
        db.execute(text("SELECT * FROM holdings WHERE account_id = 1 AND symbol = 'AAPL' FOR UPDATE;"))
        print("[Thread A] 🔒 Holding AAPL locked. Trade complete!")
        
        db.commit()
    except Exception as e:
        print(f"\n[Thread A] ❌ CRASHED: {e}")
        db.rollback()
    finally:
        db.close()

def thread_b_bad_order():
    db = SessionLocal()
    try:
        # Give Thread A a 0.5 second head start so they collide perfectly
        time.sleep(0.5) 
        
        print("[Thread B] 🔴 Started. Attempting to lock Holding AAPL...")
        db.execute(text("SELECT * FROM holdings WHERE account_id = 1 AND symbol = 'AAPL' FOR UPDATE;"))
        print("[Thread B] 🔒 Holding AAPL locked. Doing some work...")
        
        time.sleep(2)
        
        print("[Thread B] ⏳ Attempting to lock Account 1...")
        db.execute(text("SELECT * FROM accounts WHERE id = 1 FOR UPDATE;"))
        print("[Thread B] 🔒 Account 1 locked. Trade complete!")
        
        db.commit()
    except Exception as e:
        print(f"\n[Thread B] ❌ CRASHED: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    print("🚀 Starting Deadlock Simulation...")
    
    # Let's cleanly ensure the holding exists using ONLY basic columns
    setup_db = SessionLocal()
    try:
        setup_db.execute(text("DELETE FROM holdings WHERE account_id = 1 AND symbol = 'AAPL';"))
        setup_db.execute(text("""
            INSERT INTO holdings (account_id, symbol, quantity) 
            VALUES (1, 'AAPL', 10);
        """))
        setup_db.commit()
    except Exception as e:
        print(f"⚠️ Setup warning: {e}")
        setup_db.rollback()
    finally:
        setup_db.close()

    # Run both threads at the same time
    t1 = threading.Thread(target=thread_a_proper_order)
    t2 = threading.Thread(target=thread_b_bad_order)

    t1.start()
    t2.start()

    t1.join()
    t2.join()
    print("🏁 Simulation finished.")