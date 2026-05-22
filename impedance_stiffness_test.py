import asyncio
import math
import moteus

# Bare motor safe limits — retune after arm assembly
KP_BASE = 4.0        # Nm/rev from config
MAX_KP_SCALE = 0.5   # keep it safe on bare motor
MAX_TORQUE = 0.4     # Nm

async def main():
    c = moteus.Controller()
    await c.set_stop()
    await asyncio.sleep(0.3)

    # Latch current position as hold target
    state = await c.set_position(position=math.nan, velocity=0, query=True)
    hold_pos = state.values[moteus.Register.POSITION]
    kp_scale = 0.25

    print("Impedance stiffness test")
    print(f"Holding at {hold_pos:.3f} rev")
    print(f"Effective spring K = kp_base × kp_scale = {KP_BASE} × kp_scale  Nm/rev")
    print("Commands: a number (0.05–0.5) sets stiffness | 'r' rezeroes | 'q' quits")
    print("─" * 60)

    async def control_loop():
        while True:
            state = await c.set_position(
                position=hold_pos,
                velocity=0.0,
                kp_scale=kp_scale,
                kd_scale=kp_scale,   # scale damping with stiffness
                maximum_torque=MAX_TORQUE,
                query=True
            )
            pos = state.values[moteus.Register.POSITION]
            torque = state.values[moteus.Register.TORQUE]
            err = pos - hold_pos
            K_eff = KP_BASE * kp_scale
            print(
                f"\r  K={K_eff:.2f} Nm/rev  "
                f"err={err:+.4f} rev ({err*360:+.1f}°)  "
                f"torque={torque:+.3f} Nm   ",
                end="", flush=True
            )
            await asyncio.sleep(0.02)

    loop = asyncio.get_event_loop()
    task = loop.create_task(control_loop())

    try:
        while True:
            user_input = await loop.run_in_executor(
                None, input, "\nStiffness (0.05–0.5) | r=rezero | q=quit: "
            )
            cmd = user_input.strip().lower()
            if cmd == 'q':
                break
            elif cmd == 'r':
                state = await c.set_position(
                    position=math.nan, velocity=0, query=True
                )
                hold_pos = state.values[moteus.Register.POSITION]
                print(f"  → Rezeroed at {hold_pos:.3f} rev")
            else:
                try:
                    val = float(cmd)
                    kp_scale = max(0.05, min(MAX_KP_SCALE, val))
                    print(f"  → K = {KP_BASE * kp_scale:.2f} Nm/rev  (kp_scale={kp_scale})")
                except ValueError:
                    print("  → Unrecognised — try a number like 0.1 or 0.25")
    finally:
        task.cancel()
        await c.set_stop()
        print("\nStopped.")

asyncio.run(main())
