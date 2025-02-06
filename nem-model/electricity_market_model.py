import pulp
import pandas as pd
import os

# Helper functions
from helper_functions import validate_bids_against_capacity 


def solve_electricity_market(region_demand_path, generators_path, pricelevel_path, bids_path, interconnector_path):
    # Initialize the optimization problem
    model = pulp.LpProblem("Electricity_Market_Dispatch", pulp.LpMinimize)

    # Reading in CSVs 
    region_demand_raw = pd.read_csv(region_demand_path)
    generators_raw = pd.read_csv(generators_path)
    pricelevel_raw = pd.read_csv(pricelevel_path)
    bids_raw = pd.read_csv(bids_path)
    interconnector_raw = pd.read_csv(interconnector_path)

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
    # Define interconnector capacities
    interconnector_capacities = {}
    for _, row in interconnector_raw.iterrows():
        interconnector_id = row['interconnector_id']
        region_start = row['region_start']
        region_end = row['region_end']
        capacity = row['interconnector_capacity']
        
        # Initialize nested dictionaries if they don't exist
        if interconnector_id not in interconnector_capacities:
            interconnector_capacities[interconnector_id] = {}
        if region_start not in interconnector_capacities[interconnector_id]:
            interconnector_capacities[interconnector_id][region_start] = {}
            
        interconnector_capacities[interconnector_id][region_start][region_end] = capacity

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

    # Create flow variables for each interconnector using capacities from input data
    flow = {}
    for interconnector_id in interconnector_capacities:
        # Get the from_region (region_start)
        region_start = next(iter(interconnector_capacities[interconnector_id].keys()))
        
        # Get the to_region (region_end) and capacity
        region_end = next(iter(interconnector_capacities[interconnector_id][region_start].keys()))
        capacity = interconnector_capacities[interconnector_id][region_start][region_end]
        
        flow[interconnector_id] = pulp.LpVariable(
            f"flow_{interconnector_id}",
            lowBound=-capacity,
            upBound=capacity
        ) 


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
    # Region balance constraints using interconnector flow variables
    for region in regions:
        # Sum up all generation in the region
        region_generation = pulp.lpSum(gen_dispatch[region, g, p] 
                                     for g in generators[region] 
                                     for p in price_bands)
        
        # Sum up all interconnector flows affecting this region
        region_net_flow = 0
        for interconnector_id in interconnector_capacities:
            # Get the from_region and to_region for this interconnector
            from_region = next(iter(interconnector_capacities[interconnector_id].keys()))
            to_region = next(iter(interconnector_capacities[interconnector_id][from_region].keys()))
            
            # Add or subtract flow based on whether this region is source or destination
            if region == from_region:
                region_net_flow -= flow[interconnector_id]
            elif region == to_region:
                region_net_flow += flow[interconnector_id]
        
        # Add constraint: Generation +/- flows = Demand
        model += (region_generation + region_net_flow == demand[region])


    # Solve the model
    model.solve()

    # Prepare results dictionary
    results = {
        'status': pulp.LpStatus[model.status],
        'total_cost': pulp.value(model.objective),
        'dispatch': {},
        'interconnector_flow': {}
    }

    # Add flows for all defined interconnectors
    for interconnector_id in interconnector_capacities:
        from_region = next(iter(interconnector_capacities[interconnector_id].keys()))
        to_region = next(iter(interconnector_capacities[interconnector_id][from_region].keys()))
        results['interconnector_flow'][(from_region, to_region)] = pulp.value(flow[interconnector_id])

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
        'data/bids.csv',
        'data/region_interconnector.csv'
    )
    
    # Print results
    print(f"Status: {results['status']}")
    print(f"Total Cost: ${results['total_cost']:,.2f}")
    print("\nDispatch Schedule:")
    for region, generators in results['dispatch'].items():
        print(f"\nRegion {region}:")
        for generator, output in generators.items():
            print(f"{generator}: {output:.2f} MW")
    print("\nInterconnector Flows:")
    for (from_region, to_region), flow in results['interconnector_flow'].items():
        print(f"{from_region} to {to_region}: {flow:.2f} MW")