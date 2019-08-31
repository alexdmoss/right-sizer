#!/usr/bin/env python

'''
Supports the following environment variables:

RECOMMEND_ONLY = True|False. Defaults to False - so will resize pods automatically
DEBUG = True|False. Defaults to False
NAMESPACE = <string>. Useful for initial deployment - test against one namespace only. If unset, targets all namespaces
'''

import sys
import logging
from os import getenv
from kubernetes import client, config, watch
from kubernetes.config.config_exception import ConfigException
# from typing import List

logging.basicConfig(level=logging.INFO,
                    format="-> [%(levelname)s] [%(asctime)s] %(message)s",
                    datefmt="%Y-%m-%d %H:%M")

logger = logging.getLogger(__name__)


def main():

    logger.info("right-sizer has started")

    debug = getenv("DEBUG")
    if debug and debug is True:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("Debugging is enabled")

    recommend = getenv("RECOMMEND_ONLY")
    if recommend and recommend is True:
        logger.info("Running in RECOMMEND mode - pods will not be auto-resized")
        update_mode = "Off"
    else:
        logger.info("Running in UPDATE mode (default) - pods will be set to resize automatically")
        update_mode = "Auto"

    target_namespace = getenv("NAMESPACE")
    if target_namespace:
        logger.info(f"Namespace specified - VPA policy will only be created for deployments in {target_namespace}")
    else:
        logger.info("No namespace specified - ALL namespaces will be targeted with VPA policy")

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

                logger.debug(f"Found deployment {namespace}/{name}")

                try:
                    cus_obj_api.get_namespaced_custom_object(
                        "autoscaling.k8s.io",
                        "v1beta2",
                        namespace,
                        "verticalpodautoscalers",
                        name)
                    logger.debug(f"Found existing VerticalPodAutoscaler for {namespace}/{name} - will overwrite")
                except client.rest.ApiException as e:
                    if e.status == 404:
                        logger.debug(f"Did not find VerticalPodAutoscaler for {namespace}/{name} - creating")
                    else:
                        raise

                if target_namespace:
                    if target_namespace == namespace:
                        create_vpa(cus_obj_api, obj, update_mode)
                else:
                    create_vpa(cus_obj_api, obj, update_mode)


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


def create_vpa(api, obj, update_mode):
    logger.info(f"Creating VerticalPodAutoscaler for {obj.metadata.namespace}/{obj.metadata.name}")
    vpa = generate_vpa(obj, update_mode)
    try:
        api.create_namespaced_custom_object("autoscaling.k8s.io", "v1beta2", obj.metadata.namespace, "verticalpodautoscalers", vpa)
    except client.rest.ApiException as e:
        logger.error(f"Failed to create VPA policy for {obj.metadata.namespace}/{obj.metadata.name} - error was {e}")


def init():
    if __name__ == "__main__":
        sys.exit(main())


init()
