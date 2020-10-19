#!/usr/bin/env python
import requests
import sys
import time
import config

########################################################
# This script used package ID, device ID and network ID
# to create a device deployment.
# This is not a production quality code and only serves
# as an example.
########################################################

########################################################
AUTH_TOKEN = config.AUTH_TOKEN
PROJECT_ID = config.PROJECT_ID
########################################################


########################################################
DEVICE_ID = config.DEVICE_ID
PACKAGE_ID = config.PACKAGE_ID
ROUTED_NETWORK_ID = config.ROUTED_NETWORK_ID
########################################################


def wait_till_device_online():
    '''
    Poll the device status and exit when status is 'ONLINE'
    '''
    success = False
    while not success:
        print ('Waiting for device to come online')

        token = 'Bearer ' + AUTH_TOKEN
        device_details_request = requests.get(
            'https://gaapiserver.apps.rapyuta.io/api/device-manager/v0/devices/' + DEVICE_ID,
            headers={
                'Authorization': token,
                'project': PROJECT_ID
            }
        )

        if device_details_request.status_code is not 200:
            print ('API to get device details returned error: {}'.format(device_details_request.status_code))
            continue

        if device_details_request.json()['response']['data']['status'] == 'ONLINE':
            success = True
        else:
            time.sleep(2)
            continue


def wait_till_network_success():
    '''
    Poll the network status and exit when phase is SUCCEEDED and status is RUNNING
    '''
    success = False
    while not success:
        print ('Waiting for routed network to come online')

        token = 'Bearer ' + AUTH_TOKEN
        network_details_request = requests.get(
            'https://gacatalog.apps.rapyuta.io/routednetwork/' + ROUTED_NETWORK_ID,
            headers={
                'Authorization': token,
                'project': PROJECT_ID
            }
        )

        if network_details_request.status_code is not 200:
            print ('API to get network details returned error: {}'.format(network_details_request.status_code))
            continue

        if network_details_request.json()['internalDeploymentStatus']['phase'] == 'Succeeded' \
                and network_details_request.json()['internalDeploymentStatus']['status'] == 'Running':
            success = True
        else:
            time.sleep(2)
            continue



def get_device_details():
    '''
    Use device ID to get details of rapyuta.io device
    '''
    if DEVICE_ID is None:
        print ('Device ID is not known.')
        return False

    wait_till_device_online()
    print ('Device is online')

    token = 'Bearer ' + AUTH_TOKEN
    device_details_request = requests.get(
        'https://gaapiserver.apps.rapyuta.io/api/device-manager/v0/devices/' + DEVICE_ID,
        headers={
            'Authorization': token,
            'project': PROJECT_ID
        }
    )

    if device_details_request.status_code is not 200:
        print ('API to get device details returned error: {}'.format(device_details_request.status_code))
        return False

    return True


def get_network_details():
    '''
    Use routed network ID to get details of routed network.
    Returns the ip_interface of the routed network (has to be device runtime)
    '''
    if ROUTED_NETWORK_ID is None:
        print ('NETWORK ID is not known.')
        return False, None

    wait_till_network_success()
    print ('Routed network is online')

    token = 'Bearer ' + AUTH_TOKEN
    network_details_request = requests.get(
        'https://gacatalog.apps.rapyuta.io/routednetwork/' + ROUTED_NETWORK_ID,
        headers={
            'Authorization': token,
            'project': PROJECT_ID
        }
    )

    if network_details_request.status_code is not 200:
        print ('API to get network details returned error: {}'.format(network_details_request.status_code))
        return False, None

    network_details = network_details_request.json()
    ip_interface = network_details['parameters']['NETWORK_INTERFACE']

    return True, ip_interface


def get_package_details():
    '''
    Use package ID to get package details
    Returns package details
    '''
    if PACKAGE_ID is None:
        print ('Package ID is not known.')
        return False, None

    print ('Getting package details')

    token = 'Bearer ' + AUTH_TOKEN
    package_details_request = requests.get(
        'https://gacatalog.apps.rapyuta.io/serviceclass/status',
        params={
            'package_uid': PACKAGE_ID
        },
        headers={
            'Authorization': token,
            'project': PROJECT_ID
        }
    )

    if package_details_request.status_code is not 200:
        print ('API to get package details returned error: {}'.format(package_details_request.status_code))
        return False, None

    print ('Got package details')
    package_details = package_details_request.json()
    return True, package_details


def create_deployment(package_details, network_interface):
    '''
    Create a deployment in device.
    Constructs the request body using the package_details and network_interface
    Returns the deployment ID
    '''
    print ('Creating deployment')

    request_body = {
        'instance_id':'rio-instance',
        'service_id': package_details['packageInfo']['guid'],
        'plan_id': package_details['packageInfo']['plans'][0]['planId'],
        'accepts_incomplete': True,
        'organization_guid':'rio-org',
        'space_guid':'rio-space',
        'context': {
            'dependentDeployments':[],
            'component_context':{},
            'name':'server_deployment_example',
            'labels':[]
        }
    }

    routedNetworks = []
    routedNetworks.append(
        {
            'guid': ROUTED_NETWORK_ID,
            'bindParameters':{
               'NETWORK_INTERFACE': network_interface
            }
        }
    )

    request_body['context']['routedNetworks'] = routedNetworks

    component_id = package_details['packageInfo']['plans'][0]['internalComponents'][0]['componentId']
    parameters = {
        component_id:{
            'component_id': component_id,
            'device_id': DEVICE_ID
        },
        'global':{
            'device_ids': [DEVICE_ID]
        }
    }

    for param in package_details['packageInfo']['plans'][0]['components']['components'][0]['parameters']:
        parameters[component_id][param['name']] = param['default']

    request_body['parameters'] = parameters

    token = 'Bearer ' + AUTH_TOKEN
    deployment_request = requests.put(
        'https://gacatalog.apps.rapyuta.io/v2/service_instances/rio-instances',
        headers={
            'Authorization': token,
            'project': PROJECT_ID
        },
        json=request_body
    )

    if deployment_request.status_code not in [200, 202]:
        print ('API to create deployments returned error: {} - {}'.format(deployment_request.status_code, deployment_request.json()))
        return False, None

    print ('Created deployment')
    deployment_id = deployment_request.json()['operation']
    return True, deployment_id


def get_deployment_status(deployment_id):
    '''
    Continuously poll for deployment status
    '''
    if deployment_id is None:
        print ('Deployment ID is not known.')
        return

    token = 'Bearer ' + AUTH_TOKEN
    while True:
        deployment_details_request = requests.get(
            'https://gacatalog.apps.rapyuta.io/serviceinstance/' + deployment_id,
            headers={
                'Authorization': token,
                'project': PROJECT_ID
            }
        )

        if deployment_details_request.status_code is not 200:
            print ('API to get deployment status returned error: {} - {}'.format(deployment_details_request.status_code, deployment_details_request.json()))
            continue

        deployment_details = deployment_details_request.json()
        print (
            'Deployment status: status: {}, phase - {}, errors - {}'.format(
                deployment_details['status'],
                deployment_details['phase'],
                deployment_details['errors']
            )
        )
        time.sleep(1)


if __name__ == '__main__':
    try:
        if not get_device_details():
            print ('Failure in getting device details')
            sys.exit(1)

        success, ip_interface = get_network_details()
        if not success:
            print ('Failure in getting network details')
            sys.exit(1)

        success, package_details = get_package_details()
        if not success:
            print ('Failure in getting package details')
            sys.exit(1)


        success, deployment_id = create_deployment(package_details, ip_interface)
        if not success:
            print ('Failure in creating deployment')
            sys.exit(1)

        get_deployment_status(deployment_id)

    except KeyboardInterrupt:
        sys.exit(2)
