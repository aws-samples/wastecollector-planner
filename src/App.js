import {
  Flex,
  MapView,
  View,
  Button,
  Text,
  ThemeProvider,
} from "@aws-amplify/ui-react";
import { useState } from "react";
import { Amplify, API } from "aws-amplify";
import { NavigationControl, Marker, Source, Layer } from "react-map-gl";

import "@aws-amplify/ui-react/styles.css";
import awsExports from "./aws-exports";

Amplify.configure(awsExports);


const options = {
  CalculatorName: "calculatorPlaceHolder",
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
  DeparturePositions: [],
  DestinationPositions: [],
};

const theme = {
  name: "custom-button-theme",
  tokens: {
    components: {
      button: {
        fontWeight: { value: "normal" },
        link: { color: { value: "#fff" } },
      },
    },
  },
};

const lng = 12.4523;
const lat = 41.9035;
const zoom = 15;

export default function wasteMap() {
  const [bins, setBins] = useState([]);
  const [deposit, setDeposit] = useState({ longitude: 0.0, latitude: 0.0 });
  const [route, setRoute] = useState([]);
  const [toggleDeposit, setToggleDeposit] = useState(true);

  const addMarker = (lngLat) => {
    const longitude = lngLat.lng;
    const latitude = lngLat.lat;

    if (toggleDeposit) {
      setDeposit((deposit) => ({ longitude: longitude, latitude: latitude }));
    } else {
      setBins((bins) => [...bins, { longitude, latitude }]);
    }
  };

  const onMapClick = (e) => {
    const lngLat = e.lngLat.wrap();
    addMarker(lngLat);
  };

  const MarkerToDisplay = () => {
    return (
      <>
        {bins.map((b, i) => (
          <Marker {...b} key={i}>
            <img src='./recycle.png' width='35' height='35' />
          </Marker>
        ))}
        <Marker latitude={deposit.latitude} longitude={deposit.longitude}>
          <img src='./truck.png' width='35' height='25' />
        </Marker>
      </>
    );
  };

  const calculate = () => {
    document.body.style.cursor = "wait";
    const apiName = "lambdaUrl";
    const path = "/predict-path";
    const apiOptions = {
      body: options,
      headers: {
        "Content-type": "application/json",
      },
    };

    const depArr = [[deposit.longitude, deposit.latitude]];
    const binArr = bins.map((bin) => [bin.longitude, bin.latitude]);
    const positionsArray = depArr.concat(binArr);
    const routes = [];

    options.DeparturePositions = positionsArray;
    options.DestinationPositions = positionsArray;

    API.post(apiName, path, apiOptions)
      .then((response) => {
        document.body.style.cursor = "default";
        const truckRoutes = JSON.parse(response);
        let s = [];
        for (let i = 0; i < truckRoutes.length; i++) {
          let r = [];
          truckRoutes[i].forEach((path) => {
            r.push(path.Geometry.LineString);
          });
          s.push(r.flat());
        }
        setRoute(s);
      })
      .catch((error) => {
        console.log(error.response);
      });
  };

  const RouteToDisplay = () => {
    const colors = [
      "teal",
      "blue",
      "navy",
      "olive",
      "purple",
      "maroon",
      "red",
      "lime",
    ];

    return route.map((b, i) => (
      <Source
        key={i}
        type='geojson'
        data={{
          type: "Feature",
          properties: {},
          geometry: {
            type: "LineString",
            coordinates: b,
          },
        }}
      >
        <Layer
          key={i}
          type='line'
          layout={{ "line-join": "round", "line-cap": "round" }}
          paint={{
            "line-width": 5,
            "line-color": colors[Math.floor(Math.random() * colors.length)],
          }}
        />
      </Source>
    ));
  };

  return (
    <ThemeProvider theme={theme}>
      <Flex direction='row' alignItems='stretch' wrap='nowrap' gap='0rem'>
        <View
          width='15%'
          backgroundColor='rgba(35, 55, 75, 0.9)'
          padding='6px 12px'
          borderRadius='4px'
        >
          <Text color='white'>Actions</Text>
          <Flex
            direction='column'
            justifyContent='flex-start'
            alignItems='flex-start'
          >
            <Button
              variation='link'
              size='small'
              onClick={() => setToggleDeposit(true)}
            >
              Add deposit
            </Button>
            <Button
              variation='link'
              size='small'
              onClick={() => setToggleDeposit(false)}
            >
              Add bins
            </Button>
            <Button variation='link' size='small' onClick={calculate}>
              Calculate
            </Button>
            <Button variation='link' size='small'>
              Settings
            </Button>
          </Flex>
        </View>
        <MapView
          onClick={onMapClick}
          initialViewState={{
            latitude: lat,
            longitude: lng,
            zoom: zoom,
          }}
        >
          <MarkerToDisplay />
          <RouteToDisplay />
          <NavigationControl />
        </MapView>
      </Flex>
    </ThemeProvider>
  );
}
