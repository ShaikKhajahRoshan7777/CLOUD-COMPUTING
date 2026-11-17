"""Task 11 - Availability (99.9%) and 10x-load capacity planning."""
import math


def downtime(availability=0.999, days=365):
    unavail = 1 - availability
    hours = days * 24 * unavail
    return hours, hours * 60


def instances_needed(current_peak, per_instance, multiplier=10, max_util=None):
    """Instances for multiplier x peak. max_util adds headroom (e.g. 0.70)."""
    new_peak = current_peak * multiplier
    usable = per_instance * (max_util if max_util else 1)
    return new_peak, new_peak / usable, math.ceil(new_peak / usable)


if __name__ == "__main__":
    print("TASK 11.6 - AVAILABILITY")
    h, m = downtime(0.999, 365)
    print(f"99.9% per year : {h:.2f} h = {m:.1f} min")
    h30, m30 = downtime(0.999, 30)
    print(f"99.9% per month: {h30:.2f} h = {m30:.1f} min (30-day month)")

    print("\nTASK 11.5 - 10x LOAD (planning units, NOT measured traffic)")
    peak, unit = 100, 50
    new_peak, exact, n = instances_needed(peak, unit)
    print(f"New peak = 10 x {peak} = {new_peak:.0f} units; {new_peak:.0f}/{unit} = {n} instances")
    new_peak, exact, n = instances_needed(peak, unit, max_util=0.70)
    print(f"With 70% max utilisation: {new_peak:.0f}/({unit} x 0.70) = {exact:.2f} -> {n} instances")
