#!/usr/bin/env python3
"""1969 Lunar Lander simulation - Python port of lunar.bas"""

import math
import sys

# Constants from line 140 of lunar.bas
G = 1e-3
Z = 1.8


def simulation_step(altitude, velocity, mass, fuel_mass, burn_rate, time_step):
    """
    Execute one simulation step using the polynomial series from lunar.bas lines 420-430.

    Args:
        altitude: current altitude in miles
        velocity: current velocity in miles/sec (positive = downward)
        mass: total mass in lbs (capsule + fuel)
        fuel_mass: remaining fuel mass in lbs
        burn_rate: fuel burn rate in lbs/sec
        time_step: duration of this step in seconds

    Returns:
        (new_altitude, new_velocity, new_mass, new_fuel_mass, actual_time_step)
    """
    s = time_step
    k = burn_rate
    m = mass

    # Clamp burn to available fuel (line 180-190 logic)
    if m >= fuel_mass + s * k:
        # Enough fuel for full burn
        pass
    else:
        # Not enough fuel - adjust time step
        if k > 0:
            s = fuel_mass / k
        else:
            s = time_step

    # Polynomial series expansion (lines 420-430)
    q = s * k / m
    j = velocity + G * s + Z * (-q - q * q / 2 - q**3 / 3 - q**4 / 4 - q**5 / 5)
    i = altitude - G * s * s / 2 - velocity * s + Z * s * (q / 2 + q**2 / 6 + q**3 / 12 + q**4 / 20 + q**5 / 30)

    # Update state (line 330)
    new_altitude = i
    new_velocity = j
    new_mass = m - s * k
    new_fuel_mass = fuel_mass - s * k

    return new_altitude, new_velocity, new_mass, new_fuel_mass, s


def fuel_out_terminal_velocity(altitude, velocity):
    """
    Calculate terminal velocity when fuel runs out (line 240-250 of lunar.bas).

    Uses quadratic formula: s = (-v + sqrt(v^2 + 2*a*g)) / g
    Then: v_terminal = v + g*s

    Args:
        altitude: altitude when fuel runs out (miles)
        velocity: velocity when fuel runs out (miles/sec, positive = downward)

    Returns:
        terminal velocity in mph
    """
    s = (-velocity + math.sqrt(velocity * velocity + 2 * altitude * G)) / G
    v_terminal = velocity + G * s
    return 3600 * v_terminal


def touchdown_verdict(impact_velocity_mph):
    """
    Return landing verdict based on impact velocity (lines 274-300 of lunar.bas).

    Args:
        impact_velocity_mph: impact velocity in mph

    Returns:
        verdict string
    """
    w = abs(impact_velocity_mph)

    if w <= 1.2:
        return "PERFECT LANDING!"
    elif w <= 10:
        return "GOOD LANDING (COULD BE BETTER)"
    elif w <= 60:
        return "CRAFT DAMAGE... YOU'RE STRANDED HERE UNTIL A RESCUE"
    else:
        return "SORRY THERE WERE NO SURVIVORS. YOU BLOW IT!"


def main():
    """Interactive lunar lander game loop."""
    print(" " * 33 + "LUNAR")
    print(" " * 15 + "CREATIVE COMPUTING MORRISTOWN, NEW JERSEY")
    print()
    print()
    print()
    print("THIS IS A COMPUTER SIMULATION OF AN APOLLO LUNAR")
    print("LANDING CAPSULE.")
    print()
    print()
    print("THE ON-BOARD COMPUTER HAS FAILED (IT WAS MADE BY")
    print("XEROX) SO YOU HAVE TO LAND THE CAPSULE MANUALLY.")
    print()
    print("SET BURN RATE OF RETRO ROCKETS TO ANY VALUE BETWEEN")
    print("0 (FREE FALL) AND 200 (MAXIMUM BURN) POUNDS PER SECOND.")
    print("SET NEW BURN RATE EVERY 10 SECONDS.")
    print()
    print("CAPSULE WEIGHT 32,500 LBS; FUEL WEIGHT 16,500 LBS.")
    print()
    print()
    print()
    print()
    print("GOOD LUCK")

    # Initial conditions (line 140)
    l = 0  # elapsed time in seconds
    a = 120  # altitude in miles
    v = 1  # velocity in miles/sec (downward)
    m = 33000  # total mass in lbs (capsule + fuel)
    n = 16500  # capsule dry mass in lbs (constant)

    print()
    print()
    print("SEC\t\tMI + FT\t\tMPH\t\tLB FUEL\t\tBURN RATE")
    print()

    while True:
        # Display current state and get burn rate (line 150)
        altitude_miles = int(a)
        altitude_feet = int(5280 * (a - int(a)))
        mph = 3600 * v
        fuel_remaining = m - n  # m=total mass, n=dry mass, so m-n=fuel remaining

        print(f"{l}\t\t{altitude_miles} + {altitude_feet}\t\t{mph:.1f}\t\t{fuel_remaining:.1f}", end="\t\t")

        try:
            k = float(input())
        except (ValueError, EOFError):
            print("\nInvalid input. Exiting.")
            sys.exit(1)

        t = 10  # time step in seconds

        # Check for fuel out (line 160)
        if m - n < 1e-3:
            print(f"FUEL OUT AT {l} SECONDS")
            s = (-v + math.sqrt(v * v + 2 * a * G)) / G
            v = v + G * s
            l = l + s
            w = 3600 * v
            print(f"ON MOON AT {l:.1f} SECONDS - IMPACT VELOCITY {w:.2f} MPH")
            verdict = touchdown_verdict(w)
            print(verdict)
            # Print follow-up flavor text (lines 286, 310)
            if 10 < w <= 60:
                print("PARTY ARRIVES. HOPE YOU HAVE ENOUGH OXYGEN!")
            elif w > 60:
                print(f"IN FACT, YOU BLASTED A NEW LUNAR CRATER {w * 0.227:.1f} FEET DEEP!")
            break

        # Simulate time step (lines 170-230)
        while t >= 1e-3:
            a, v, m, fuel_mass, s = simulation_step(a, v, m, m - n, k, t)
            l = l + s
            t = t - s

            # Check for landing (line 200-220)
            if a <= 0:
                w = 3600 * v
                print(f"ON MOON AT {l:.1f} SECONDS - IMPACT VELOCITY {w:.2f} MPH")
                verdict = touchdown_verdict(w)
                print(verdict)
                if 10 < w <= 60:
                    print("PARTY ARRIVES. HOPE YOU HAVE ENOUGH OXYGEN!")
                elif w > 60:
                    print(f"IN FACT, YOU BLASTED A NEW LUNAR CRATER {w * 0.227:.1f} FEET DEEP!")
                sys.exit(0)

            # Check for fuel out mid-step
            if m - n < 1e-3:
                print(f"FUEL OUT AT {l} SECONDS")
                s = (-v + math.sqrt(v * v + 2 * a * G)) / G
                v = v + G * s
                l = l + s
                w = 3600 * v
                print(f"ON MOON AT {l:.1f} SECONDS - IMPACT VELOCITY {w:.2f} MPH")
                verdict = touchdown_verdict(w)
                print(verdict)
                if 10 < w <= 60:
                    print("PARTY ARRIVES. HOPE YOU HAVE ENOUGH OXYGEN!")
                elif w > 60:
                    print(f"IN FACT, YOU BLASTED A NEW LUNAR CRATER {w * 0.227:.1f} FEET DEEP!")
                sys.exit(0)


if __name__ == "__main__":
    main()
