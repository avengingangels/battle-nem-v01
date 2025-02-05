import pulp
import pandas as pd
import os

# Helper functions
from helper_functions import validate_bids_against_capacity 


def solve_electricity_market(region_demand_path, generators_path, pricelevel_path, bids_path):
    # Initialize the optimization problem
    model = pulp.LpProblem("Electricity_Market_Dispatch", pulp.LpMinimize)

    # Reading in CSVs 
    region_demand_raw = pd.read_csv(region_demand_path)
    generators_raw = pd.read_csv(generators_path)
    pricelevel_raw = pd.read_csv(pricelevel_path)
    bids_raw = pd.read_csv(bids_path)

    # Data validation
    # Validate that the bids do not exceed capacity
    if not validate_bids_against_capacity(generators_raw, bids_raw):
        raise ValueError("Bids exceed generator capacity")

    # Define regions
    regions = list(region_demand_raw['region'])

    #Define demand
    demand = dict(zip(region_demand_raw['region'], region_demand_raw['demand']))

    # Define generators and their capacities
    generators = {}
    for _, row in generators_raw.iterrows():
        region = row['region']
        generator_name = row['generator_name']
        nameplate_capacity = row['nameplate_capacity']
        
        if region not in generators:
            generators[region] = {}
        generators[region][generator_name] = nameplate_capacity


    # Define price bands
    price_bands = list(pricelevel_raw['pricelevel'])

    # Create bid structure (for this example, distributing capacity evenly across bands)
    bids = {}
    for region in regions:
        bids[region] = {}
        for gen in generators[region]:
            bids[region][gen] = {}
            for _, bid_row in bids_raw[bids_raw['generator_name'] == gen].iterrows():
                price_band = bid_row['pricelevel']
                bids[region][gen][price_band] = bid_row['bid_capacity']  


    # Decision variables: generation for each generator at each price band
    gen_dispatch = pulp.LpVariable.dicts("generation",
        ((r, g, p) for r in regions for g in generators[r] for p in price_bands),
        lowBound=0)

    # Interconnector flow variable (positive means flow from NSW to VIC)
    flow = pulp.LpVariable("interconnector_flow", -50, 50)  # ±50 MW limit

    # Objective function: minimize total cost
    model += pulp.lpSum(
        gen_dispatch[r, g, p] * p
        for r in regions
        for g in generators[r]
        for p in price_bands
    )

    # Constraints
    # 1. Generator capacity constraints
    for r in regions:
        for g in generators[r]:
            for p in price_bands:
                model += gen_dispatch[r, g, p] <= bids[r][g][p]
            # Total generation across all price bands can't exceed capacity
            model += pulp.lpSum(gen_dispatch[r, g, p] for p in price_bands) <= generators[r][g]

    # 2. Demand balance constraints

    # Region 1 balance: Generation - Flow = Demand
    model += (pulp.lpSum(gen_dispatch['NSW', g, p] 
        for g in generators['NSW'] 
        for p in price_bands) - flow == demand['NSW'])

    # Region 2 balance: Generation + Flow = Demand
    model += (pulp.lpSum(gen_dispatch['VIC', g, p] 
        for g in generators['VIC'] 
        for p in price_bands) + flow == demand['VIC'])


    # Solve the model
    model.solve()

    # Prepare results dictionary
    results = {
        'status': pulp.LpStatus[model.status],
        'total_cost': pulp.value(model.objective),
        'dispatch': {},
        'interconnector_flow': pulp.value(flow)
    }

    # Collect dispatch results
    for r in regions:
        results['dispatch'][r] = {}
        for g in generators[r]:
            total_gen = sum(pulp.value(gen_dispatch[r, g, p]) for p in price_bands)
            results['dispatch'][r][g] = total_gen

    return results

# Example usage:
if __name__ == "__main__":
    results = solve_electricity_market(
        'data/region_demand.csv',
        'data/generators.csv',
        'data/pricelevel.csv',
        'data/bids.csv'
    )
    
    # Print results
    print(f"Status: {results['status']}")
    print(f"Total Cost: ${results['total_cost']:,.2f}")
    print("\nDispatch Schedule:")
    for region, generators in results['dispatch'].items():
        print(f"\nRegion {region}:")
        for generator, output in generators.items():
            print(f"{generator}: {output:.2f} MW")
    print(f"\nInterconnector Flow (NSW to VIC): {results['interconnector_flow']:.2f} MW") 