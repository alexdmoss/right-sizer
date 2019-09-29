#!/usr/bin/env python

'''
Supports the following environment variables:

    UPDATE_MODE = Off|Auto. Defaults to Off - recommendations mode only
    DEBUG = True|False. Defaults to False
    NAMESPACE = <string>. Useful for initial deployment - test against one namespace only. If unset, targets all namespaces

'''

import sys
import logging
from os import getenv

from kubernetes import client, config, watch
from kubernetes.config.config_exception import ConfigException

import right_sizer.vpa as vpa
import right_sizer.patch as patch
import right_sizer.utils as utils

logging.basicConfig(level=logging.INFO,
                    format="-> [%(levelname)s] [%(asctime)s] %(message)s",
                    datefmt="%Y-%m-%d %H:%M")

logger = logging.getLogger(__name__)

if getenv("DEBUG"):
    logging.getLogger().setLevel(logging.DEBUG)
    logger.debug("Debugging is enabled")


def main():

    logger.info("right-sizer has started")

    update_mode = utils.set_update_mode()
    target_namespace = utils.set_namespace()
    patch_kube_system = utils.set_patch_kube_system()
    update_frequency = utils.set_update_frequency()

    try:
        config.load_incluster_config()  # on cluster
    except ConfigException:
        config.load_kube_config()  # fallback to local

    while True:

        w = watch.Watch()

        if patch_kube_system:
            patch.patch_kube_system_resources()

        # this has a timeout which prevents "spam patching" above
        watch_for_deployments(w, target_namespace, update_mode, update_frequency)


def watch_for_deployments(w, target_namespace, update_mode, update_frequency):

    apps_v1_api = client.AppsV1Api()
    cus_obj_api = client.CustomObjectsApi()

    for event in w.stream(apps_v1_api.list_deployment_for_all_namespaces, timeout_seconds=int(update_frequency)):

        if event["type"] == "ADDED":

            obj = event["object"]

            name = obj.metadata.name
            namespace = obj.metadata.namespace

            logger.debug(f"Found deployment {namespace}/{name}")

            if target_namespace:

                if namespace == target_namespace:

                    if not vpa.does_vpa_exist(cus_obj_api, namespace, name):

                        logger.info(f"Did not find VerticalPodAutoscaler for {namespace}/{name} - CREATING")
                        vpa.create_vpa(cus_obj_api, obj, update_mode)

                    else:
                        logger.info(f"Found existing VerticalPodAutoscaler for {namespace}/{name} - SKIPPING")

            else:

                if not vpa.does_vpa_exist(cus_obj_api, namespace, name):

                    logger.info(f"Did not find VerticalPodAutoscaler for {namespace}/{name} - CREATING")
                    vpa.create_vpa(cus_obj_api, obj, update_mode)

                else:
                    logger.info(f"Found existing VerticalPodAutoscaler for {namespace}/{name} - SKIPPING")


def init():

    if __name__ == "__main__":
        sys.exit(main())


init()
