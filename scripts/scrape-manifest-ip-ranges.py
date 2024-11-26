#!/usr/bin/env python3
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

# This script provides data validation around the bloxtool CLI, which
# retrieves Mozilla IP address ranges froma third party vendor. The
# script runs as a recurring systemd task.

import ipaddress
import json
import logging
import subprocess
import sys
import time
from pathlib import Path

import requests
from datadiff import diff
from voluptuous import (
    All,
    Any,
    In,
    Invalid as VoluptuousInvalid,
    Optional,
    Schema,
    truth,
)
from voluptuous.humanize import validate_with_humanized_errors


formatter = logging.Formatter("%(name)s %(message)s")
formatter.converter = time.gmtime
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(formatter)
logger = logging.getLogger("mozilla-ip-scraper")
logger.addHandler(handler)


def write_to_file_atomically(file_path: Path, content: str) -> None:
    """Writes new data to a temp file, then renames the temp
    file to the existing filename"""
    temp_file_path = file_path.with_suffix(".tmp")
    with temp_file_path.open(mode="w") as temp_file:
        temp_file.write(content)

    temp_file_path.rename(file_path)


@truth
def is_ip_address_network(value: str) -> bool:
    """Validates if a given value (interpreted as a str) represents
    an IP address network"""
    try:
        # This call will raise a ValueError if value is not a valid ip address range
        ipaddress.ip_network(value, strict=True)
        return True

    except ValueError:
        return False


@truth
def all_required_aws_regions_exist(prefixes: list) -> bool:
    """Validates that the set of all required AWS regions is a subset
    of all the regions in the iterable of IP networks"""
    required_regions = {"us-west-2"}

    prefixes_in_new_document = {prefix_object["region"] for prefix_object in prefixes}

    return required_regions <= prefixes_in_new_document


@truth
def all_required_gcp_regions_exist(prefixes: list) -> bool:
    """Validates that the set of all required GCP regions is a subset
    of all the regions in the iterable of IP networks"""
    required_regions = {
        "northamerica-northeast1",
        "us-central1",
        "us-west1",
    }

    prefixes_in_new_document = {prefix_object["scope"] for prefix_object in prefixes}

    return required_regions <= prefixes_in_new_document


@truth
def all_required_azure_regions_exist(values: list) -> bool:
    """Checks if all required Azure regions (in lowercase) are present in the
    'properties.region' field for entries where the 'name' field starts with 'Storage.'."""

    # Define the required Azure regions in lowercase
    required_regions = {
        "canadacentral",
        "centralindia",
        "centralus",
        "eastus",
        "eastus2",
        "northcentralus",
        "northeurope",
        "southindia",
        "westus",
        "westus2",
        "westus3",
    }

    # Extract the regions from the 'name' field where the region appears after "Storage."
    regions_in_new_document = {
        value["properties"]["region"].lower()
        for value in values
        if value["name"].startswith("Storage.")
    }

    # Validate that all required regions are present
    return required_regions <= regions_in_new_document


def get_mozilla_office_ips():
    """Entry point for the Mozilla office IP scraper

    Calls out to bloxtool to obtain Mozilla network information
    in JSON format. Validates the JSON against a known schema and
    atomically re-writes a file with the CIDR representations of
    Mozilla office IP address spaces.
    """
    try:
        mozilla_ip_ranges_file = Path("/var/hg/moz-ip-ranges.txt")
        bloxtool_config_file = Path("/etc/mercurial/bloxtool.ini")
        bloxtool_command = [
            "/var/hg/venv_tools/bin/bloxtool",
            "network",
            "search",
            "attribute",
            "subnet-purpose",
            "value",
            "nat-pool",
            "--format=json",
            f"--config={bloxtool_config_file}",
        ]

        bloxtool_json_schema = Schema(
            [
                {
                    "comment": str,
                    "_ref": str,
                    "network": is_ip_address_network,
                    "network_view": str,
                }
            ],
            extra=False,
            required=True,
        )

        # Get raw string output and convert to Python dict
        process_output = subprocess.run(
            bloxtool_command, check=True, encoding="utf-8", stdout=subprocess.PIPE
        ).stdout
        output_as_dict = json.loads(process_output)

        # Verify dict schema
        validate_with_humanized_errors(output_as_dict, bloxtool_json_schema)

        write_to_file_atomically(
            mozilla_ip_ranges_file, "\n".join(i["network"] for i in output_as_dict)
        )

    except subprocess.CalledProcessError as cpe:
        logger.exception(
            "An error occurred while executing the bloxtool command: exit code %s"
            % cpe.returncode
        )
        logger.exception("STDOUT: %s" % cpe.stdout)
        logger.exception("STDERR: %s" % cpe.stderr)
        sys.exit(1)

    except json.JSONDecodeError as jde:
        logger.exception(
            "An error occurred parsing the bloxtool output as JSON: %s" % jde.msg
        )
        sys.exit(1)

    except VoluptuousInvalid as vi:
        logger.exception(
            "The JSON data from bloxtool does not match the required schema."
        )
        logger.exception("Error message: %s" % vi.msg)
        logger.exception("Error path: %s" % vi.path)
        logger.exception("Exception message: %s" % vi.error_message)
        sys.exit(1)


def get_aws_ips():
    """Entry point for the AWS IP address scraper

    Downloads the AWS IP ranges JSON document from Amazon and verifies against a
    known schema. Atomically rewrites a file with the CIDR representations of
    AWS IP address spaces.
    """
    try:
        # Grab the new data from Amazon
        amazon_ip_ranges_file = Path("/var/hg/aws-ip-ranges.json")
        ip_ranges_response = requests.get(
            "https://ip-ranges.amazonaws.com/ip-ranges.json"
        )

        # Ensure 200 OK response code
        if ip_ranges_response.status_code != 200:
            sys.exit("HTTP response from Amazon was not 200 OK")

        # Sanity check: ensure the file is an appropriate size
        if len(ip_ranges_response.content) < 88000:
            sys.exit(
                "The retrieved AWS JSON document is smaller than the minimum allowable file size"
            )

        # JSON Schema for the Amazon IP Ranges JSON document
        amazon_json_schema = Schema(
            {
                "syncToken": str,
                "createDate": str,
                "ipv6_prefixes": [
                    dict
                ],  # If IPv6 is supported in the future, this will need to be defined
                # The prefixes field must meet both requirements:
                # 1. There must be at least one entry for each region containing CI and S3 bundles
                # 2. Must be a list of dicts that fit the schema below
                "prefixes": All(
                    all_required_aws_regions_exist,
                    [
                        {
                            "ip_prefix": is_ip_address_network,
                            "region": str,
                            "service": str,
                            "network_border_group": Optional(str),
                        },
                    ],
                ),
            },
            extra=False,
            required=True,
        )

        # Validate dict schema
        output_as_dict = ip_ranges_response.json()
        validate_with_humanized_errors(output_as_dict, amazon_json_schema)

        # Sanity check: ensure the syncToken indicates an IP space change has been made
        # since the last recorded change. Only check if a file exists, in case of new deployments
        if amazon_ip_ranges_file.is_file():
            file_bytes = amazon_ip_ranges_file.read_bytes()
            existing_document_as_dict = json.loads(file_bytes)

            file_diff = diff(existing_document_as_dict, output_as_dict, context=0)

            # Exit if the file contents are the same or the syncToken has not changed
            if not file_diff or int(output_as_dict["syncToken"]) <= int(
                existing_document_as_dict["syncToken"]
            ):
                sys.exit()

        else:
            existing_document_as_dict = (
                {}
            )  # No existing document means whole file is the diff
            file_diff = diff(existing_document_as_dict, output_as_dict, context=0)

        write_to_file_atomically(amazon_ip_ranges_file, json.dumps(output_as_dict))

        # Print the diff for collection as systemd unit output
        logger.info("AWS IP ranges document has been updated")
        logger.info(file_diff)

    except subprocess.CalledProcessError as cpe:
        logger.exception(
            "An error occurred when notifying about changes to the file: exit code %s"
            % cpe.returncode
        )
        logger.exception("STDOUT: %s" % cpe.stdout)
        logger.exception("STDERR: %s" % cpe.stderr)
        sys.exit(1)

    except json.JSONDecodeError as jde:
        logger.exception(
            "An error occurred parsing the data retrieved from Amazon as JSON: %s"
            % jde.msg
        )
        sys.exit(1)

    except VoluptuousInvalid as vi:
        logger.exception(
            "The JSON data from Amazon does not match the required schema."
        )
        logger.exception("Error message: %s" % vi.msg)
        logger.exception("Error path: %s" % vi.path)
        logger.exception("Exception message: %s" % vi.error_message)
        sys.exit(1)


def get_gcp_ips():
    """Entry point for the GCP IP address scraper.

    Downloads the GCP IP ranges JSON document from Google and verifies against a
    known schema. Atomically rewrites a file with the CIDR representations of
    GCP IP address spaces.
    """
    try:
        # Grab the new data from Amazon
        gcp_ip_ranges_file = Path("/var/hg/gcp-ip-ranges.json")
        ip_ranges_response = requests.get("https://www.gstatic.com/ipranges/cloud.json")

        # Ensure 200 OK response code
        if ip_ranges_response.status_code != 200:
            sys.exit("HTTP response from Google was not 200 OK")

        # Sanity check: ensure the file is an appropriate size
        if len(ip_ranges_response.content) < 8000:
            sys.exit(
                "The retrieved GCP JSON document is smaller than the minimum allowable file size"
            )

        # JSON Schema for the Google IP Ranges JSON document
        google_json_schema = Schema(
            {
                "syncToken": str,
                "creationTime": str,
                # The prefixes field must meet both requirements:
                # 1. There must be at least one entry for each region containing CI and S3 bundles
                # 2. Must be a list of dicts that fit the schema below
                "prefixes": All(
                    all_required_gcp_regions_exist,
                    [
                        {
                            # One of these tags must be present, and it's value must be an IP block.
                            In({"ipv4Prefix", "ipv6Prefix"}): is_ip_address_network,
                            "scope": str,
                            "service": str,
                        },
                    ],
                ),
            },
            extra=False,
            required=True,
        )

        # Validate dict schema
        output_as_dict = ip_ranges_response.json()
        validate_with_humanized_errors(output_as_dict, google_json_schema)

        # Sanity check: ensure the syncToken indicates an IP space change has been made
        # since the last recorded change. Only check if a file exists, in case of new deployments
        if gcp_ip_ranges_file.is_file():
            file_bytes = gcp_ip_ranges_file.read_bytes()
            existing_document_as_dict = json.loads(file_bytes)

            file_diff = diff(existing_document_as_dict, output_as_dict, context=0)

            # Exit if the file contents are the same or the syncToken has not changed
            if not file_diff or int(output_as_dict["syncToken"]) <= int(
                existing_document_as_dict["syncToken"]
            ):
                sys.exit()

        else:
            existing_document_as_dict = (
                {}
            )  # No existing document means whole file is the diff
            file_diff = diff(existing_document_as_dict, output_as_dict, context=0)

        write_to_file_atomically(gcp_ip_ranges_file, json.dumps(output_as_dict))

        # Print the diff for collection as systemd unit output
        logger.info("GCP IP ranges document has been updated")
        logger.info(file_diff)

    except subprocess.CalledProcessError as cpe:
        logger.exception(
            "An error occurred when notifying about changes to the file: exit code %s"
            % cpe.returncode
        )
        logger.exception("STDOUT: %s" % cpe.stdout)
        logger.exception("STDERR: %s" % cpe.stderr)
        sys.exit(1)

    except json.JSONDecodeError as jde:
        logger.exception(
            "An error occurred parsing the data retrieved from GCP as JSON: %s"
            % jde.msg
        )
        sys.exit(1)

    except VoluptuousInvalid as vi:
        logger.exception("The JSON data from GCP does not match the required schema.")
        logger.exception("Error message: %s" % vi.msg)
        logger.exception("Error path: %s" % vi.path)
        logger.exception("Exception message: %s" % vi.error_message)
        sys.exit(1)


def get_azure_ips():
    """Entry point for the Azure IP address scraper.

    Downloads the Azure IP ranges JSON document and verifies against a
    known schema. Atomically rewrites a file with the CIDR representations of
    Azure IP address spaces.
    """
    try:
        # Define the file path for storing Azure IP ranges
        azure_ip_ranges_file = Path("/var/hg/azure-ip-ranges.json")

        # Fetch the latest Azure IP ranges from the URL
        ip_ranges_response = requests.get(
            "https://raw.githubusercontent.com/mozilla-platform-ops/azure-public-ip-ranges/refs/heads/main/az_ips.json"
        )

        # Ensure the HTTP response is successful
        if ip_ranges_response.status_code != 200:
            sys.exit("HTTP response from Azure IP ranges was not 200 OK")

        # Sanity check: ensure the file is not unexpectedly small
        if len(ip_ranges_response.content) < 8000:
            sys.exit(
                "The retrieved Azure JSON document is smaller than the minimum allowable file size"
            )

        # Define the schema for validating the Azure IP ranges document
        azure_json_schema = Schema(
            {
                "changeNumber": int,
                "cloud": str,
                "values": All(
                    all_required_azure_regions_exist,  # Validate required Azure regions
                    [
                        {
                            "name": str,  # Ensure this contains "Storage.$REGION"
                            "id": str,
                            "properties": {
                                "changeNumber": int,
                                "region": str,
                                "regionId": int,
                                "platform": str,
                                "systemService": str,
                                "addressPrefixes": [
                                    is_ip_address_network
                                ],  # Validate each IP network
                                "networkFeatures": Any(list, None),
                            },
                        }
                    ],
                ),
            },
            extra=False,
            required=True,
        )

        # Parse the Azure IP ranges JSON data
        output_as_dict = ip_ranges_response.json()

        # Validate the parsed data against the schema
        validate_with_humanized_errors(output_as_dict, azure_json_schema)

        # Sanity check: if the file exists, ensure there's a change in content
        if azure_ip_ranges_file.is_file():
            existing_file_bytes = azure_ip_ranges_file.read_bytes()
            existing_document_as_dict = json.loads(existing_file_bytes)

            file_diff = diff(existing_document_as_dict, output_as_dict, context=0)

            # Exit if the file contents are unchanged
            if not file_diff:
                sys.exit()

        # If no existing file, everything is considered new
        else:
            existing_document_as_dict = {}
            file_diff = diff(existing_document_as_dict, output_as_dict, context=0)

        # Write the new data to the file atomically
        write_to_file_atomically(azure_ip_ranges_file, json.dumps(output_as_dict))

        # Log the changes to the systemd unit output
        logger.info("Azure IP ranges document has been updated")
        logger.info(file_diff)

    except requests.exceptions.RequestException as re:
        logger.exception(f"An error occurred while retrieving Azure IP ranges: {re}")
        sys.exit(1)

    except json.JSONDecodeError as jde:
        logger.exception(
            "An error occurred parsing the data retrieved from Azure as JSON: %s"
            % jde.msg
        )
        sys.exit(1)

    except VoluptuousInvalid as vi:
        logger.exception("The JSON data from Azure does not match the required schema.")
        logger.exception("Error message: %s" % vi.msg)
        logger.exception("Error path: %s" % vi.path)
        logger.exception("Exception message: %s" % vi.error_message)
        sys.exit(1)


# Register possible commands
COMMANDS = {
    "aws": get_aws_ips,
    "azure": get_azure_ips,
    "gcloud": get_gcp_ips,
    "moz-offices": get_mozilla_office_ips,
}


if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in COMMANDS:
        sys.exit(
            "usage: {executable} <{possible_commands}>".format(
                executable=sys.argv[0], possible_commands=" | ".join(COMMANDS.keys())
            )
        )

    COMMANDS[sys.argv[1]]()
    sys.exit()
