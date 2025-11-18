"""
Diagnostic script to identify why resampling causes infeasibility.

Run this before and after resampling to see what changes.
"""
import pandas as pd
import numpy as np

def diagnose_network(network, label="Network"):
    """Print diagnostic information about the network."""
    print(f"\n{'='*80}")
    print(f"{label} DIAGNOSTICS")
    print(f"{'='*80}")

    # Snapshot information
    print(f"\n[Snapshots]")
    print(f"  Count: {len(network.snapshots)}")
    if len(network.snapshots) > 1:
        try:
            # Try to convert to DatetimeIndex if it's not already
            import pandas as pd
            if not isinstance(network.snapshots, pd.DatetimeIndex):
                snapshots = pd.DatetimeIndex(network.snapshots)
            else:
                snapshots = network.snapshots

            freq = (snapshots[1] - snapshots[0]).total_seconds() / 3600
            print(f"  Frequency: {freq} hours")
            print(f"  Total hours: {len(snapshots) * freq}")
        except Exception as e:
            print(f"  Frequency: Could not calculate ({e})")
            print(f"  Snapshot type: {type(network.snapshots)}")

    # Generator capacity
    print(f"\n[Generator Capacity]")
    for carrier in network.generators.carrier.unique():
        carrier_gens = network.generators[network.generators.carrier == carrier]
        total_p_nom = carrier_gens.p_nom.sum()
        print(f"  {carrier}: {total_p_nom:.0f} MW")

        # Check p_max_pu if it exists
        if hasattr(network.generators_t, 'p_max_pu') and not network.generators_t.p_max_pu.empty:
            for gen_name in carrier_gens.index:
                if gen_name in network.generators_t.p_max_pu.columns:
                    p_max_pu = network.generators_t.p_max_pu[gen_name]
                    print(f"    {gen_name}: p_max_pu mean={p_max_pu.mean():.3f}, max={p_max_pu.max():.3f}, min={p_max_pu.min():.3f}")

    # Energy constraints
    print(f"\n[Energy Constraints]")
    if 'e_sum_max' in network.generators.columns:
        for carrier in network.generators.carrier.unique():
            carrier_gens = network.generators[network.generators.carrier == carrier]
            e_sum_max = carrier_gens.e_sum_max.sum()
            e_sum_min = carrier_gens.e_sum_min.sum() if 'e_sum_min' in carrier_gens.columns else 0
            print(f"  {carrier}:")
            print(f"    e_sum_max: {e_sum_max:.0f} MWh")
            print(f"    e_sum_min: {e_sum_min:.0f} MWh")

    # Load information
    print(f"\n[Load]")
    if hasattr(network.loads_t, 'p_set') and not network.loads_t.p_set.empty:
        total_load = network.loads_t.p_set.sum().sum()
        avg_load = network.loads_t.p_set.sum(axis=1).mean()
        peak_load = network.loads_t.p_set.sum(axis=1).max()
        print(f"  Total energy: {total_load:.0f} MWh")
        print(f"  Average power: {avg_load:.0f} MW")
        print(f"  Peak power: {peak_load:.0f} MW")

    # Ramp limits
    print(f"\n[Ramp Limits]")
    if 'ramp_limit_up' in network.generators.columns:
        for carrier in network.generators.carrier.unique():
            carrier_gens = network.generators[network.generators.carrier == carrier]
            if carrier_gens.ramp_limit_up.notna().any():
                avg_ramp = carrier_gens.ramp_limit_up.mean()
                print(f"  {carrier}: ramp_limit_up={avg_ramp:.3f}")

    # Check for potential issues
    print(f"\n[Potential Issues]")

    # Check if renewable capacity can meet load
    try:
        if hasattr(network.generators_t, 'p_max_pu') and hasattr(network.loads_t, 'p_set'):
            if not network.generators_t.p_max_pu.empty and not network.loads_t.p_set.empty:
                for snapshot in network.snapshots[:5]:  # Check first 5 snapshots
                    available_gen = 0
                    for gen_name in network.generators.index:
                        p_nom = network.generators.loc[gen_name, 'p_nom']
                        if gen_name in network.generators_t.p_max_pu.columns:
                            p_max_pu = network.generators_t.p_max_pu.loc[snapshot, gen_name]
                            available_gen += p_nom * p_max_pu
                        else:
                            available_gen += p_nom  # Assume fully available

                    total_load = network.loads_t.p_set.loc[snapshot].sum()

                    if available_gen < total_load:
                        print(f"  WARNING: Snapshot {snapshot}: Available gen ({available_gen:.0f} MW) < Load ({total_load:.0f} MW)")
                        print(f"           Deficit: {total_load - available_gen:.0f} MW")
            else:
                print("  No time-series data available for load-generation check")
        else:
            print("  No time-series data available for load-generation check")
    except Exception as e:
        print(f"  Could not check load-generation balance: {e}")

    print(f"\n{'='*80}\n")


def compare_resampling_effect(network, weights=4):
    """
    Show the effect of resampling on key variables.
    """
    print(f"\n{'='*80}")
    print(f"RESAMPLING EFFECT ANALYSIS (weights={weights})")
    print(f"{'='*80}")

    # Analyze p_max_pu for renewable generators
    if hasattr(network.generators_t, 'p_max_pu') and not network.generators_t.p_max_pu.empty:
        print(f"\n[p_max_pu Resampling Effect]")

        for gen_name in network.generators_t.p_max_pu.columns[:5]:  # First 5 generators
            original = network.generators_t.p_max_pu[gen_name]

            # Simulate resampling
            resampled_mean = original.resample(f'{weights}H').mean()
            resampled_max = original.resample(f'{weights}H').max()

            print(f"\n  {gen_name}:")
            print(f"    Original:  mean={original.mean():.3f}, max={original.max():.3f}")
            print(f"    Mean rule: mean={resampled_mean.mean():.3f}, max={resampled_max.max():.3f}")
            print(f"    Max rule:  mean={resampled_max.mean():.3f}, max={resampled_max.max():.3f}")
            print(f"    Loss with mean rule: {(original.mean() - resampled_mean.mean())/original.mean()*100:.1f}%")


if __name__ == "__main__":
    print("Import this module and use:")
    print("  diagnose_network(network, 'Before Resampling')")
    print("  diagnose_network(network, 'After Resampling')")
    print("  compare_resampling_effect(network, weights=4)")
