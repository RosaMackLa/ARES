import asyncio
import math
import moteus

MAX_VEL = 5.0   # rev/s max (~300 RPM) — safe for your 3A PSU
MAX_TORQUE = 0.5  # Nm

async def main():
    c = moteus.Controller()
    await c.set_stop()
    
    current_vel = 0.0
    print("Motor speed controller")
    print(f"Range: {-MAX_VEL} to {MAX_VEL} rev/s | 'q' to quit | Enter to stop")
    print("─" * 50)

    async def control_loop():
        while True:
            state = await c.set_position(
                position=math.nan,
                velocity=current_vel,
                maximum_torque=MAX_TORQUE,
                query=True
            )
            pos = state.values[moteus.Register.POSITION]
            vel = state.values[moteus.Register.VELOCITY]
            fault = state.values[moteus.Register.FAULT]
            print(f"\r  vel_cmd={current_vel:+.2f}  actual={vel:+.3f}  pos={pos:.3f}  fault={fault}   ", end="", flush=True)
            await asyncio.sleep(0.05)

    loop = asyncio.get_event_loop()
    task = loop.create_task(control_loop())

    try:
        while True:
            user_input = await loop.run_in_executor(None, input, "\nSpeed (rev/s): ")
            if user_input.strip().lower() == 'q':
                break
            try:
                val = float(user_input)
                val = max(-MAX_VEL, min(MAX_VEL, val))
                current_vel = val
                print(f"  → Set to {current_vel:+.2f} rev/s")
            except ValueError:
                current_vel = 0.0
                print("  → Stopped")
    finally:
        task.cancel()
        await c.set_stop()
        print("\nStopped.")

asyncio.run(main())
