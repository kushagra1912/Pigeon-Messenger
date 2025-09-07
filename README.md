# P02-Pigeon

## Overview

Pigeon is a secure E2EE instant messaging application. It consists of a client and server subsystem, found in pigeon-client and pigeon-server respectively. Refer to either directory for detailed instructions on how to install, deploy and run each subsystem. A Pigeon server must be running for communication between clients to take place.

## Team Members

- Abdullah Badat
- Kaitlyn Lake (Team Captain)
- Aryaman Tiwari
- Kushagra Agrawal
- Sanchit Jain
- Anshul Dadhwal
- Krisna Bou


# Pigeon Client

## Description

These are the commands to run everything related to Pigeon Client

### Running

The native method is the recommended usage

### Through docker

To build and run the docker image, run the `run.sh` script

### Natively

Install the dependencies with

`poetry install`

Run the application with

`poetry run python client/main.py`

## Unit testing

### Client tests

To run client tests, run below in `/pigeon-client/client`

`poetry run python -m unittest unit-tests`

### Integration tests

Integration tests require an active server. Deploy or run the server as described in `P02-Pigeon/pigeon-server/`

Once server is up, to run integration test, run below in `/pigeon-client/client`
`poetry run python -m unittest integration-tests`

## Troubleshooting

If the client is failing to connect to the server, double check the URL in `api.txt` matches the URL of the server

# Pigeon Server

To start up the server run:
`./deploy.sh`

To kill the server run:
`terraform destroy -auto-approve`

The url for the server is available in `../pigeon-client/client/api.txt`

## k6 testing

Located in the `/pigeon-server`

`k6 run load.js`