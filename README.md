# Optimize Waster collection with Amazon Location Services and Amazon SageMaker 

## Routing optimization for waste bin collection
In everyday life we often use routing services to get directions on how to get from point A (i.e. home) to point B (i.e. work). Behind the scenes of these services, there are algorithms that calculate the best way to reach point B from point A and provide with the best route depending on the mode of transportation, traffic conditions and many other parameters.  

[Amazon Location Service](https://aws.amazon.com/location/) has released a feature that allows you to define a list of routes from a set of starting points to a set of destination points. This list is used as input for a route planning algorithm. A route planning algorithm is the process of computing the most effective path from one place to another through several stops. Logistics, transport and deliveries companies use route planning software to compile the required routes.  

This blog post will show how to use Amazon Location Service and an optimization algorithm to find the most efficient route for a waste collection optimization problem. Waste collection is the transfer of waste from the point of disposal to the point of treatment. This transfer is typically done using garbage trucks. 


## Security

See [CONTRIBUTING](CONTRIBUTING.md#security-issue-notifications) for more information.

## License

This library is licensed under the MIT-0 License. See the LICENSE file.


## What we are going to build.
In this post we will describe how to build a web application to help optimize routing for garbage collection across the city with an interactive GUI. You will define the starting point of the garbage trucks, the location of the bins, the number of trucks in the fleet and their dimensions with just few clicks on the map displayed on your browser.

Before building the front end, you will build and test the back end with the optimization algorithm using [Amazon SageMaker](https://aws.amazon.com/sagemaker/?nc2=h_ql_prod_ml_sm). The algorithm optimizes routes of all trucks according to the following constraints:  
*	the current traffic status.  
*	a truck can only travel roads suitable for the vehicle (height, width and mass).  
*	the maximum capacity represented as number of trash bins that can be collected by a single truck
*	all trucks at the end of the garbage collection process should return to the starting point where the garbage disposal center is located.

The optimal routes will then be displayed back on our GUI to receive feedback over the output of the optimization process.  

![Figure 1 – Application Screenshot showing route optimization outcome](./images/image.png)   

**Figure 1 – Application Screenshot showing route optimization outcome**


## Solution Overview
Route planning is not as simple as planning a route from point A to point B, this was discussed in a previous blog post [Amazon Location Service enables Matrix Routing to optimize route planning](https://aws.amazon.com/it/blogs/mobile/amazon-location-service-enables-matrix-routing-to-optimize-route-planning/). Routes may have multiple points of departure, such as point A and B, and multiple destinations positions, such as X and Y. To plan and optimize routes from A and B to X and Y, you will need the travel time and travel distance for all of the potential routes within the matrix. The calculation of time, or distance, between each combination of points makes up a **route matrix**.      

To leverage the Matrix Routing feature to solve your problem, you will consider each bin both as an end-point of a hop and also as a starting-point for the next hop.  
![Figure 2 – Bins are both start and end point in this complex routing problem](./images/image-1.png)

**Figure 2 – Bins are both start and end point in this complex routing problem**

This enables you to retrieve all possible distances from any one bin to all the others. As you can see the size of the problem already starts to increase: if you have a home location and 9 bins then you get a 10 x 10 Routing Matrix (100 values). SageMaker can help build the algorithm and deploy it as a serverless inference end-point by also enabling a pay-per-use cost model for our application.  

The overall architecture you will build is described below:  
 
![Figure 3 – Overall architecture](./images/image-2.png)  

**Figure 3 – Overall architecture**

The complete architecture is dived in three parts loosely coupled.

1. The front-end is a React Application that leverages [AWS Amplify](https://aws.amazon.com/amplify/?nc=sn&loc=1) client libraries to connect to AWS services. You can pin bins and the truck deposit on the map, send the coordinates to the AWS Lambda function and draw the optimal path on the map after receiving the optimal routes.  

2.  The Lambda function interacts with Amazon Location passing the coordinates of the bins and getting the route matrix. Then it sends the route matrix to a SageMaker endpoint where the algorithm calculates the optimal route for all the trucks and returns all the routes back to the Lambda function.  

3.  The route geometries are sent back to the browser for visualization on the map.  

You will deploy the components using two [AWS CloudFormation](https://aws.amazon.com/cloudformation/) templates:
*  **setup_environment.yaml**   - creates the Amazon Location services and the associated policy  
*  **api_gateway_template.yaml**  - creates the Amazon API Gateway, the Lambda function and Amazon Cognito identity pool for unauthenticated access to Amazon Location.  



## Amazon Location and Amazon SageMaker  
The problem you are going to solve is a capacity constrained [Vehicle Routing Problem](https://en.wikipedia.org/wiki/Vehicle_routing_problem). It is similar to a travelling salesperson problem (TSP) with some differences. There are more than trucks that are going to be used to cover all the bins and each truck has a limited capacity in terms of bins that it can collect.  
This algorithm is NP hard ([non-deterministic polynomial-time](https://en.wikipedia.org/wiki/NP_(complexity)) hardness), that means that the computational effort needed to find the best solution grows exponentially with the number of bins to be collected. To be able to solve this problem, a set of different algorithms and libraries have been developed in order to find a sub-optimal solution in a reasonable amount of time.  
To keep the implementation of the solution simple we will use [Google Optimization Tools](https://developers.google.com/optimization) (a.k.a., OR-Tools). It is an open-source, fast and portable software suite for solving combinatorial optimization problems. OR-Tools are written in C++, but they provide **wrappers in Python**, C# and Java.  

Before designing and coding the web application, let’s take some time to experiment with Amazon Location and the vehicle routing algorithm using an Amazon SageMaker Studio Notebook.  


### Set up the environment  
In this post you will use CloudFormation to build a SageMaker Studio environment and create the following resources:
-	SageMaker Studio Domain to build and deploy the optimization algorithm and experiment with Location services
-	Location service Map service to interact with maps
-	Location service Routing service to compute routes
-	Provide the right grants to SageMaker to access to the former services.


The CloudFormation template used in this step is named setup_environment.yaml and can be downloaded from [here](https://raw.githubusercontent.com/aws-samples/wastecollector-planner/main/CFTemplate/setup_environment.yaml).
In order to deploy CloudFormation template you can use the AWS Console using this [link](https://us-east-1.console.aws.amazon.com/cloudformation).  
This will open a new window in your browser similar to Figure 4:  
#####################################################  
ADD IMAGE HERE
#####################################################    
**Figure 4 – AWS CloudFormation Console**  

You can now click on **Create stack**, in the next form select **Upload a template file** and use the **Choose file button** to upload the previously downloaded template.
Then click **Next** and fill **Stack name** field with: **LocationServiceDemo** and leave all other Parameters to their default values.
Select  **Next** and **Next** again and in the last screen acknowledge that CloudFormation is going to create AWS Identity and Access Management (IAM) resources as shown in Figure 5 and then click **Submit**.
#####################################################  
ADD IMAGE HERE
##################################################### 
**Figure 5 –CloudFormation acknowledge IAM resource creation**  

Wait until the CloudFormation stack creation process completes. At the end you will see something similar to Figure 6.
#####################################################  
ADD IMAGE HERE
##################################################### 
**Figure 6 – AWS CloudFormation check completion**  

After the stack creates all the resources you can access SageMaker Studio using this [link](https://us-east-1.console.aws.amazon.com/sagemaker/home?region=us-east-1#/studio) and in the console you see your resources similar to Figure 7.  
#####################################################  
ADD IMAGE HERE
##################################################### 
**Figure 7 – Amazon SageMaker Studio console**  

Here you can click on **MyDomain** and this is going to open a new window listing the available users in the domain. In order to open SageMaker Studio environment, select **Launch** and then **Studio** as shown in Figure 8.  
#####################################################  
ADD IMAGE HERE
##################################################### 
**Figure 8 – Amazon SageMaker Studio open user console**  

Now that you have opened SageMaker Studio you will use the included feature to clone the repository https://github.com/aws-samples/wastecollector-planner by clicking on the git icon on the left, selecting **Clone Repository** on the left panel, typing the repository name in the combo box and selecting the hint provided by the combo “Clone https://github.com/aws-samples/wastecollector-planner" and then pressing the button **Clone** as shown in Figure 9.
#####################################################  
ADD IMAGE HERE
##################################################### 
**Figure 9 – Amazon SageMaker Studio cloning github repository**  

Browse the SageMaker Notebook local folders using the panel on the left and open the notebook used for experimenting with Amazon Location. 
The notebook is located in **wastecollector-planner/SageMaker/Using Sagemaker-OR-Tools.ipynb**. Double-click on it.
You will be prompted to select the kernel to be used for this notebook and the **Datascience** kernel will already be selected, if not browse in the list of available kernels and select **Datascience**. Now the notebook will open showing all steps described hereafter. You can execute the steps by clicking on the play icon in the Notebook’s tool bar.

After installing all the required libraries on your Notebook, you are going to deploy a SageMaker inference endpoint to invoke OR-Tools from inside the notebook to test them and also to expose them as a service to be invoked from outside the notebook.
To build an inference endpoint in SageMaker, go through steps in the notebook to build and test the estimator and deploy it with an interface endpoint. 

OR-Tools does not need a training phase, at least when dealing with a small number of items included in the path. You can start to find the optimal route considering a random initialization, so you can build a SageMaker Model ready to be deployed. You just need to provide SageMaker Model with an algorithm using a container and initial weights generated during the training phase, an empty file in our example.


### Building Sagemaker Model  
In order to set-up the container that includes our algorithm you are going to use a “use-your-own-script” [approach](https://aws.amazon.com/it/blogs/machine-learning/bring-your-own-model-with-amazon-sagemaker-script-mode/). This approach leverages existing containers prepared by Amazon, for most common frameworks like Tensorflow, Pythorch, Mxnet, SKLearn, by passing to them a custom script containing the algorithm and an additional file (requirements.txt) with a list of libraries.

In this example, you are going to use a [SKLearn](https://docs.aws.amazon.com/sagemaker/latest/dg/pre-built-docker-containers-scikit-learn-spark.html) container. For this specific example you do not need to use a predefined initial condition for your route optimization problem and since you do not need to run a training phase, you will build a dummy training output file, upload it to Amazon Simple Storage Service (Amazon S3) and build your model by calling SKLearnModel object. 

```
from  sagemaker.sklearn.model import SKLearnModel
modelName=f"RouteOptimiser-{timestamp}"
sklearn_preprocessor = SKLearnModel(
    role=role,
    predictor_cls  = sagemaker.predictor.Predictor,
    sagemaker_session = sagemaker_session,
    name=modelName,
    model_data=f"s3://{bucket}/{prefix}/{timestamp}/model.tar.gz",
    source_dir = 'scripts-or-tools',
    entry_point= 'algorithm.py',
    framework_version ='0.23-1'
)
```



### Deploy Sagemaker Model  
Once the model is ready, we are going to deploy a Sagemaker Serverless Inference end-point providing information about the amount of memory to allocate and the maximum number of concurrent calls. We also want the endpoint to use json as input and output data format.  
![image-5.png](./images/image-5.png)  

### Testing our algorithm  
The algorithm is now ready to be used by the frontend application. Let’s test it before deploying. We will instruct Sagemaker to run Amazon Location Services, which is going to generate test data to visualize the result. Sagemaker will ask Location Service to create a route calculator and a map service for us.  
![image-6.png](./images/image-6.png)  
We are now ready to leverage location services to obtain a Route Matrix.  
We can specify additional constraints that the service has to take into account, i.e: the size of our truck, making sure we are not going through too small streets, the weight and other attributes.  
Every point is going to be a starting point and an endpoint of a hop in our Route Matrix.  

![image-7.png](./images/image-7.png)  

After extracting relevant data from the response and putting them in a matrix format, we will have:  
    array([  
        [0, 0.812, 0.731, 0.679],  
        [0.824, 0, 0.674, 0.622],  
        [0.787, 0.718, 0, 0.263],  
        [0.88, 0.963, 1.09, 0],  
    ]);  


The matrix is not symmetric and this is due to the one-way signs that require different routes: to go from 0 to 3 the distance is 0.67 KM while to go from 3 to 0 it is 0.88 KM.
We can now send the matrix to the Optimization Algorithm to get the best routes. 

![image-8.png](./images/image-8.png)

We will get the following output: [[0, 3, 2, 1, 0]]. 
This is an array of a single item. Since we asked to optimize routes for a single track, the meaning of the output is that we start from point 0 through points 3,2,1 and then back to 0. 
The number that represents each point, can be transformed back into GPS coordinates and displayed on a map.

![image-9.png](./images/image-9.png)  

### Using Sagemaker Endpoint from external services  
You now need to implement a REST API that helps to expose a service that
recieves as input the list of locations of garbage bins and returns the
information needed to plot the optimized route on a map.

The implementation of this service has been done using the following
architecture:

![](./images/image11.png)

The Lambda function performs all the required preprocessing steps like interacting with Amazon Location services to compute the Route Matrix and than invokes Sagemaker endpoint to perform the route optimiziation. As Sagemaker returns the answer, the Lambda function computes the route geometry and sends them back to API Gateway that returns the answer to the caller.

We are going to use nodeJS to implement our lambda function and we need to include the latest version of the AWS Javascript SDK. Since this library can be reused by multiple lambda functions we decided to build a custom lambda layer to host that.

You can integrate the lamba layer following the directions described here:

https://aws.amazon.com/premiumsupport/knowledge-center/lambda-layer-aws-sdk-latest-version/

You have to install the following packages as layer:

    npm install @aws-sdk/client-location
    npm install @aws-sdk/client-sagemaker-runtime

This is what the Lambda function is doing in detail:

1.  Calculate the route matrix starting from parameters passed by the web app

The Lambda function make use of AWS SDK for Javascript V3 and calculate the route matrix starting from parameters passed by the browser and stored into matrixParams variable.

    try {
        const client = new LocationClient({region: region});
        const command = new CalculateRouteMatrixCommand(matrixParams);
        const routeMatrix = await client.send(command);
    }
    catch {...}

matrixParams is a JSON sent by the web application with all the relevant information to calculate the route matrix.

    const options = {
        DepartNow: true,
        IncludeLegGeometry: true,
        DistanceUnit: "Kilometers",
        TravelMode: "Truck",
        TruckModeOptions: {
            AvoidFerries: true,
            AvoidTolls: true,
            Dimensions: {
            Height: 2.5,
            Length: 4.95,
            Unit: "Meters",
            Width: 1.8,
            },
            Weight: {
            Total: 1000,
            Unit: "Kilograms",
            },
        },
        DeparturePositions: [[longitude, latitude]],
        DestinationPositions: [[longitude, latitude]],
    };

Where DeparturePositions is an array of longitude, latitude of the truck deposit and DestinationPositions is a matrix with the coordinates of all the bins.

You can find detailed info about all the options at the following link:

<https://docs.aws.amazon.com/AWSJavaScriptSDK/v3/latest/clients/client-location/interfaces/calculateroutematrixcommandinput.html#departurepositions>

2.  Calculate the route matrix starting from parameters passed by the web app

Call the Sagemaker endpoint passing to it the route matrix (from point 1) and getting back the optimal routes:

    try {
        const client = new SageMakerRuntimeClient({ region: region });
        const command = new InvokeEndpointCommand(input);
        const data = await client.send(command);
        var optimal = new TextDecoder().decode(data.Body);
    }
    catch {...}

3.  With the optimal routes (from point 2), Lambda calls Location services to get the route geometry and pass it back to the web app.

Call the CalculateRouteCommand and get back the geometry of the single routes:

    try {
        const client = new LocationClient({region: region});
        const command = new CalculateRouteCommand(matrixParams);
        const leg = await client.send(command);
    }
    catch {...}


A role must be in place for Lambda to call Amazon Location services and
Sagemaker, the role is:

A role must be in place for Lambda to call Amazon Location services and Sagemaker.
The role is created by the cloudformation template (apigateway_lambda_template.yaml) based on the policy from the first one (setup_environment.yaml).
So, to deploy API Gateway, Lambda function and related roles you can use the [apigateway_lambda_template.yaml](https://github.com/aws-samples/wastecollector-planner/blob/main/CFTemplate/apigateway_template.yaml) cloudformation template.

You have to provide in input:

-   the name of Sagemaker Endpoint (we can get it from the Jupyter notebook)

-   the ARN of the Lambda Layer you have already created

-   the name of the policy that shall be used to access Location
    Services (you can get it from the output of the first cloudformation
    template we used to set-up the environment)

-   the name of the Location Service Calculator instace that shall be
    used by the lambda function (you can get it from the output of the first cloudformation
    template we used to set-up the environment).

Once the cloudformation template execution completes we can get the following values from its output:

-   The url of the REST api we have just built

-   The Cognito Identity Pool ID, UserPoolID and AppClientIDWeb that are used by the web app 

## Building the Web App  
In this section you will build the web app that makes use of the
optimization algorithm exposed by Sagemaker inference endpoint as
described above.

The web app will utilize React and make use of the Amplify Javascript
Library and Amazon Location Services, to display the map on the web
page.

You will not use the Amplify CLI in this project because all the backend
services are created using the CloudFormation templates.

When using the Amplify CLI, the **aws-exports.js** file gets created and updated automatically for you based on the resources you have added and configured. If you are not using the Amplify CLI as in our case, you need to create the file and fill in with data coming from the output of the Cloudformation templates. 

In the repository, you just need to open the file [aws-exports.js.template](https://github.com/aws-samples/wastecollector-planner/blob/main/src/aws-exports.js.template), insert with the correct information and save it as **aws-exports.js**

You are now ready to run the web app with:

    npm install
    npm run build
    nom run start

When done, point your browser to

    http://localhost:8080/

And have fun!

### CODE Walkthrough

The React application make use of:

**Amplify Javascript Library** - open-source client libraries that
provide use-case centric, opinionated, declarative, and easy-to-use
interfaces enabling developers to easily interact with their backends.

<https://docs.amplify.aws/lib/q/platform/js/>

**Amplify UI -** a collection of accessible, themeable, performant React
components

<https://ui.docs.amplify.aws/>

**react-map-gl** -- A react wrapper for Mapbox GL JS Map

<https://visgl.github.io/react-map-gl/>

The client code can be downloaded from
<https://github.com/aws-samples/wastecollector-planner/tree/main/src>

## Clean up

To clean up just follow the instruction described at the end of the Sagemaker notebook and the delete the two cloudformation templates.
