# rio_example_client

See [rapyuta.io user docs](https://userdocs.rapyuta.io/) for more info on the rapyuta platform.

This example script uses package ID, device ID and routed network ID to make a rapyuta.io deployment on the given device. The script first waits for the device and routed network to be online, then creates a deployment using the package details and then monitors the status of the deployment.

This is not a production quality code and only serves as an example.

#### Assumptions:
1. The routed network is deployed as a device runtime. i.e. it is a [device routed network](https://userdocs.rapyuta.io/build-solutions/sample-walkthroughs/routed-network/#creating-device-routed-network)
2. The package consists of a single plan and a single component.
3. The same network interface selected when creating the device routed network is used when deploying the package.

## Config variables

The file `config.py` contains tokens and IDs. Please edit the file with the desired values before running he script.


    ########################################################
    AUTH_TOKEN = ''
    PROJECT_ID = ''
    ########################################################


    ########################################################
    DEVICE_ID = ''
    PACKAGE_ID = ''
    ROUTED_NETWORK_ID = ''  # (Device runtime)
    ########################################################


## Running the script

Simply invoke the script from the root of the repository.

    ./run_deployment_example.py