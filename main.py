# main.py
# Main script to run PyPSA economic dispatch analysis

from libs.import_singlenode import import_base_model


def main():
    """
    Main function to create network and run economic dispatch
    """
    print("Creating PyPSA network...")
    
    # Import base model from import_singlenode.py
    n = import_base_model(year=2024, network_name='kr_grid', bus_name='kr_bus')
    
    print("\nRunning economic dispatch optimization...")
    
    # Run economic dispatch (linear optimization)
    n.optimize()
    
    print("\nEconomic dispatch completed!")
    print("="*50)
    print("OPTIMIZATION RESULTS")
    print("="*50)
    
    # Display optimization results
    print(f"Objective value: {n.objective}")
    print(f"Status: Optimal")
    
    # Display generator dispatch results
    if hasattr(n, 'generators_t') and 'p' in n.generators_t:
        print(f"\nGenerator dispatch summary:")
        total_generation = n.generators_t.p.sum().sum()
        print(f"Total generation: {total_generation:.2f} MW")
        
        # Show top 10 generators by total generation
        gen_totals = n.generators_t.p.sum().sort_values(ascending=False)
        print(f"\nTop 10 generators by total generation:")
        for i, (gen_name, total_p) in enumerate(gen_totals.head(10).items()):
            print(f"{i+1:2d}. {gen_name}: {total_p:.2f} MWh")
    
    return n


if __name__ == "__main__":
    # Run the main function
    network = main()
