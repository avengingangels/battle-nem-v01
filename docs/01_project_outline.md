
# Introduction

In this project I will start by creating an electricity market model using PuLP

# Objective function
The objective is create a model where I can provide a schedule of bids for each generator in the market, and then solve for the optimal dispatch schedule.

# Key Features

The model should have at least two regions. This means there should be an interregional transmission constraint.
The model should operate for a single time interval.
Each generator belongs to a region.
Each generator has a maximum capacity that it can dispatch.

Generators bid their capacity into the market in four pre-specified price points.

Where possible, the model should separate out information regarding model values (such as generation capacity) from the linear programming model itself.

# Output of model

The model should produce a dispatch schedule.
It should also produce the regional price for each region.
Note that the regional price is the price of the marginal unit of generation in each region.

