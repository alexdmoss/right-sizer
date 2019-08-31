#!/usr/bin/env python

import sys
import logging
from argparse import ArgumentParser
from kubernetes import client, config, watch
from kubernetes.config.config_exception import ConfigException
# from typing import List

logging.basicConfig(level=logging.INFO,
                    format="-> [%(levelname)s] [%(asctime)s] %(message)s",
                    datefmt="%Y-%m-%d %H:%M")

logger = logging.getLogger(__name__)


def main():

    logger.info("right-sizer has started")

    parser = ArgumentParser()
    parser.add_argument("--recommend", help="VPA are created in recommend (updateMode: off) mode only", action="store_true")
    parser.add_argument("-v", "--debug", help="Turn on debugging", action="store_true")
    args = parser.parse_args()

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("Debugging is enabled")

    if args.recommend:
        logger.info("Running in RECOMMEND mode - pods will not be auto-resized")
        update_mode = "Off"
    else:
        logger.info("Running in UPDATE mode (default) - pods will be set to resize automatically")
        update_mode = "Auto"

    try:
        config.load_incluster_config()  # on cluster
    except ConfigException:
        config.load_kube_config()  # fallback to local

    apps_v1_api = client.AppsV1Api()
    cus_obj_api = client.CustomObjectsApi()

    while True:

        w = watch.Watch()

        for event in w.stream(apps_v1_api.list_deployment_for_all_namespaces, timeout_seconds=600):

            obj = event["object"]

            # only care when a new object is added
            if event["type"] == "ADDED":

                name = obj.metadata.name
                namespace = obj.metadata.namespace

                logger.info(f"Found deployment {namespace}/{name}")

                # Temporary safety check
                if namespace == "mw-platform":

                    try:
                        cus_obj_api.get_namespaced_custom_object(
                            "autoscaling.k8s.io",
                            "v1beta2",
                            namespace,
                            "verticalpodautoscalers",
                            name)
                        logger.debug(f"Found existing VPA for {namespace}/{name} - will overwrite")
                    except client.rest.ApiException as e:
                        if e.status == 404:
                            logger.debug(f"Did not find VPA for {namespace}/{name} - creating")
                        else:
                            raise

                    vpa = generate_vpa(obj, update_mode)

                    create_vpa(cus_obj_api, vpa, namespace, name)

    logger.info("Script completed")


def generate_vpa(obj, update_mode):
    vpa = {
        "apiVersion": "autoscaling.k8s.io/v1beta2",
        "kind": "VerticalPodAutoscaler",
        "metadata": {
            "name": obj.metadata.name,
            "namespace": obj.metadata.namespace,
            "ownerReferences": [
                {
                    "apiVersion": obj.api_version,
                    "blockOwnerDeletion": False,
                    "controller": True,
                    "kind": obj.kind,
                    "name": obj.metadata.name,
                    "uid": obj.metadata.uid,
                },
            ],
        },
        "spec": {
            "targetRef": {
                "apiVersion": obj.api_version,
                "kind": obj.kind,
                "name": obj.metadata.name,
                "namespace": obj.metadata.namespace,
            },
            "updatePolicy": {
                "updateMode": update_mode
            }
        }
    }

    logger.debug(f"Generated VPA Object: {vpa}")

    return vpa


def create_vpa(api, vpa, namespace, name):
    logger.info(f"Creating VerticalPodAutoscaler for {namespace}/{name}")
    try:
        api.create_namespaced_custom_object("autoscaling.k8s.io", "v1beta2", namespace, "verticalpodautoscalers", vpa)
    except client.rest.ApiException as e:
        logger.error(f"Failed to create VPA policy for {namespace}/{name} - error was {e}")


def init():
    if __name__ == "__main__":
        sys.exit(main())


init()
