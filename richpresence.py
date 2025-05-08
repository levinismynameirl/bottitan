from pypresence import Presence
import time

def update_presence():
    # Create a Presence instance
    RPC = Presence("1354462298034667661")
    RPC.connect()
    
    while True:
        try:
            RPC.update(
                state="Online",
                details="Assisting the Executive Command Board",
                start=int(time.time()),  # Current timestamp
                large_image="ecblgosss",
                large_text="Numbani",
                small_image="logo",
                small_text="Rogue - Level 100",
                party_id="ae488379-351d-4a4f-ad32-2b9b01c91657",
                party_size=[0, 5]
            )
            time.sleep(15)  # Discord rate limit is 15 seconds
        except Exception as e:
            print(f"Error updating presence: {e}")
            time.sleep(15)

if __name__ == "__main__":
    try:
        update_presence()
    except KeyboardInterrupt:
        print("Presence Disconnected")