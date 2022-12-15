from __future__ import print_function

import csv
import json
import numpy as np
import pandas as pd
import boto3

import os
import argparse

from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp

from sagemaker_containers.beta.framework import (
    content_types, encoders, env, modules, transformer, worker)
    

    
#####
#Sagemaker interface
#####
def model_fn (model_dir):
    print ("ModelFN")
    return ("DUMMY MODEL")

def input_fn(input_data, content_type):
    """Parse input data payload

    We currently only take csv input. Since we need to process both labelled
    and unlabelled data we first determine whether the label column is present
    by looking at how many columns were provided.
    """
    print ("InputFN")
    print ("content_type:",content_type)
    print ("input_data:",input_data)
    if content_type == 'application/json':
        # Read the raw input data as CSV.
        list=json.loads(input_data)
        #Catching multiple nested json to string encapsulation 
        if (type(list)==str):
            list=json.loads(input_data)
        if (type(list)==str):
            list=json.loads(input_data)
        return list
    else:
        raise ValueError("{} not supported by script!".format(content_type))


def output_fn(prediction, accept):
    """Format prediction output

    The default accept/content-type between containers for serial inference is JSON.
    We also want to set the ContentType or mimetype as the same value as accept so the next
    container can read the response payload correctly.
    """
    if accept == "application/json":
 
        if prediction['result']!='NOT FOUND':
            data=prediction['data']
            manager=prediction['manager']
            routing=prediction['routing']
            solution=prediction['solution']

            """Prints solution on console."""
            routes=[]
            print(f'Objective: {solution.ObjectiveValue()}')
            max_route_distance = 0
            for vehicle_id in range(data['num_vehicles']):
                index = routing.Start(vehicle_id)
                plan_output = 'Route for vehicle {}:\n'.format(vehicle_id)
                route_distance = 0
                route=[]
                while not routing.IsEnd(index):
                    plan_output += ' {} -> '.format(manager.IndexToNode(index))
                    route.append(manager.IndexToNode(index))
                    previous_index = index
                    index = solution.Value(routing.NextVar(index))
                    route_distance += routing.GetArcCostForVehicle(
                        previous_index, index, vehicle_id)

                plan_output += '{}\n'.format(manager.IndexToNode(index))
                route.append(manager.IndexToNode(index))
                plan_output += 'Distance of the route: {}m\n'.format(route_distance)
                print(plan_output)
                routes.append(route)
                max_route_distance = max(route_distance, max_route_distance)
            print('Maximum of the route distances: {}m'.format(max_route_distance))
        else:
            routes='NOT FOUND'
        return (json.dumps(routes))

    else:
        raise RuntimeException("{} accept type is not supported by this script.".format(accept))

def predict_fn(input_data, model):
    """Preprocess input data

    We implement this because the default predict_fn uses .predict(), but our model is a preprocessor
    so we want to use .transform().

    The output is returned in the following order:

        rest of features either one hot encoded or standardized
    """
    # Create the routing index manager.
    manager = pywrapcp.RoutingIndexManager(len(input_data['distance_matrix']),
                                           input_data['num_vehicles'], input_data['depot'])

    # Create Routing Model.
    routing = pywrapcp.RoutingModel(manager)

    # Create and register a transit callback.
    def distance_callback(from_index, to_index):
        """Returns the distance between the two nodes."""
        # Convert from routing variable Index to distance matrix NodeIndex.
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        return input_data['distance_matrix'][from_node][to_node]

    transit_callback_index = routing.RegisterTransitCallback(distance_callback)

    # Define cost of each arc.
    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)
    
    # Create and register a demand callback.
    def demand_callback(from_index):
        """Returns the demand of the node."""
        # Convert from routing variable Index to demands NodeIndex.
        from_node = manager.IndexToNode(from_index)
        #Consume a slot
        return 1

    demand_callback_index = routing.RegisterUnaryTransitCallback(demand_callback)

    routing.AddDimensionWithVehicleCapacity(
        demand_callback_index,
        0,  # null capacity slack
        input_data['vehicle_capacities'],  # vehicle maximum capacities
        True,  # start cumul to zero
        'Capacity')



    # Add Distance constraint.
    dimension_name = 'Distance'
    routing.AddDimension(
        transit_callback_index,
        0,  # no slack
        3000,  # vehicle maximum travel distance
        True,  # start cumul to zero
        dimension_name)
    distance_dimension = routing.GetDimensionOrDie(dimension_name)
    distance_dimension.SetGlobalSpanCostCoefficient(5000)

    # Setting first solution heuristic.
    search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    search_parameters.first_solution_strategy = (
        routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC)

    search_parameters.local_search_metaheuristic = (
        routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH)
    search_parameters.time_limit.FromSeconds(10)


    # Solve the problem.
    solution = routing.SolveWithParameters(search_parameters)
    if solution:
        prediction={
            'data':input_data,
            'manager':manager,
            'routing':routing,
            'solution':solution,
            'result':'OK'
        }
    else:
        prediction={'result':'NOT FOUND'}
    return prediction


##Dummy Training Function

if __name__ == '__main__':

    # Sagemaker specific arguments. Defaults are set in the environment variables.    
    parser = argparse.ArgumentParser()

    parser.add_argument('--model-dir', type=str, default=os.environ['SM_MODEL_DIR'])

    args = parser.parse_args()
    
    
    with open( os.path.join(args.model_dir, "model.data"), 'w') as f:
        f.write('ok')
        f.close()
    print("mode saved!")
    
