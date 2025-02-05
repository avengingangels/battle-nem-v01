def validate_bids_against_capacity(generator_input, bids_input):
    """
    Validates that the sum of bids for each generator does not exceed its nameplate capacity.
    
    Args:
        generator_input (pd.DataFrame): DataFrame containing generator information with columns 
                                      ['region', 'generator_name', 'nameplate_capacity']
        bids_input (pd.DataFrame): DataFrame containing bid information with columns
                                 ['generator_name', 'pricelevel', 'bid_capacity']
    
    Returns:
        bool: True if all generators' bid sums are within capacity, False otherwise
    """
    # Group bids by generator and sum their bid capacities
    total_bids = bids_input.groupby('generator_name')['bid_capacity'].sum()
    
    # Create a dictionary of generator capacities for easy lookup
    generator_capacities = dict(zip(generator_input['generator_name'], 
                                  generator_input['nameplate_capacity']))
    
    # Check each generator's total bids against its capacity
    for generator in total_bids.index:
        if generator not in generator_capacities:
            return False
        if total_bids[generator] > generator_capacities[generator]:
            return False
            
    return True
