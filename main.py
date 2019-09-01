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

logging.basicConfig(level=logging.INFO,
                    format="-> [%(levelname)s] [%(asctime)s] %(message)s",
                    datefmt="%Y-%m-%d %H:%M")

logger = logging.getLogger(__name__)


def main():

    logger.info("right-sizer has started")

    debug = getenv("DEBUG")

    if debug and debug == 'True':
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("Debugging is enabled")

    update_mode = getenv("UPDATE_MODE")
    if update_mode == 'Auto':
        logger.info("Running in UPDATE mode - pods will be set to resize automatically")
    else:
        logger.info("Running in RECOMMEND mode (default) - pods will not be auto-resized")
        update_mode = "Off"

    target_namespace = getenv("NAMESPACE")

    if target_namespace:
        logger.info(f"Namespace specified - VPA policy will only be created for deployments in {target_namespace}")
    else:
        logger.info("No namespace specified - ALL namespaces will be targeted with VPA policy")

    try:
        config.load_incluster_config()  # on cluster
    except ConfigException:
        config.load_kube_config()  # fallback to local

    while True:

        w = watch.Watch()

        patch_kube_system_resources()

        create_vpas_for_deployments(w, target_namespace, update_mode)


def create_vpas_for_deployments(w, target_namespace, update_mode):

    apps_v1_api = client.AppsV1Api()
    cus_obj_api = client.CustomObjectsApi()

    for event in w.stream(apps_v1_api.list_deployment_for_all_namespaces, timeout_seconds=600):

        if event["type"] == "ADDED":

            obj = event["object"]

            name = obj.metadata.name
            namespace = obj.metadata.namespace

            logger.debug(f"Found deployment {namespace}/{name}")

            if target_namespace:

                if namespace == target_namespace:

                    if not does_vpa_exist(cus_obj_api, namespace, name):

                        logger.info(f"Did not find VerticalPodAutoscaler for {namespace}/{name} - CREATING")
                        create_vpa(cus_obj_api, obj, update_mode)

                    else:
                        logger.info(f"Found existing VerticalPodAutoscaler for {namespace}/{name} - SKIPPING")

            else:

                if not does_vpa_exist(cus_obj_api, namespace, name):

                    logger.info(f"Did not find VerticalPodAutoscaler for {namespace}/{name} - CREATING")
                    create_vpa(cus_obj_api, obj, update_mode)

                else:
                    logger.info(f"Found existing VerticalPodAutoscaler for {namespace}/{name} - SKIPPING")


def patch_kube_system_resources():

    patch = {
        "spec": {
            "template": {
                "spec": {
                    "containers": [
                        {
                            "name": "kubedns",
                            "resources": {
                                "requests": {
                                    "cpu": "10m",
                                    "memory": "50Mi",
                                },
                                "limits": {
                                    "cpu": "100m",
                                    "memory": "100Mi",
                                }
                            }
                        }
                    ]
                }
            }
        }
    }
    logger.info("Patching kube-dns:kubedns with lower resource requests/limits")
    patch_deployment(name='kube-dns', patch=patch)

    patch = {
        "spec": {
            "template": {
                "spec": {
                    "containers": [
                        {
                            "name": "dnsmasq",
                            "resources": {
                                "requests": {
                                    "cpu": "10m",
                                    "memory": "20Mi",
                                },
                                "limits": {
                                    "cpu": "100m",
                                    "memory": "50Mi",
                                }
                            }
                        }
                    ]
                }
            }
        }
    }
    logger.info("Patching kube-dns:dnsmasq with lower resource requests/limits")
    patch_deployment(name='kube-dns', patch=patch)

    patch = {
        "spec": {
            "template": {
                "spec": {
                    "containers": [
                        {
                            "name": "heapster",
                            "resources": {
                                "requests": {
                                    "cpu": "10m",
                                    "memory": "20Mi",
                                },
                                "limits": {
                                    "cpu": "20m",
                                    "memory": "50Mi",
                                }
                            }
                        }
                    ]
                }
            }
        }
    }
    logger.info("Patching heapster with lower resource requests/limits")
    patch_deployment(name='heapster-v1.6.1', patch=patch)

    patch = {
        "spec": {
            "template": {
                "spec": {
                    "containers": [
                        {
                            "name": "heapster-nanny",
                            "resources": {
                                "requests": {
                                    "cpu": "10m",
                                    "memory": "20Mi",
                                },
                                "limits": {
                                    "cpu": "20m",
                                    "memory": "50Mi",
                                }
                            }
                        }
                    ]
                }
            }
        }
    }
    logger.info("Patching heapster-nanny with lower resource requests/limits")
    patch_deployment(name='heapster-v1.6.1', patch=patch)

    patch = {
        "spec": {
            "template": {
                "spec": {
                    "containers": [
                        {
                            "name": "metrics-server",
                            "resources": {
                                "requests": {
                                    "cpu": "10m",
                                    "memory": "20Mi",
                                },
                                "limits": {
                                    "cpu": "20m",
                                    "memory": "50Mi",
                                }
                            }
                        }
                    ]
                }
            }
        }
    }
    logger.info("Patching metrics-server with lower resource requests/limits")
    patch_deployment(name='metrics-server-v0.3.1', patch=patch)

    patch = {
        "spec": {
            "template": {
                "spec": {
                    "containers": [
                        {
                            "name": "metrics-server-nanny",
                            "resources": {
                                "requests": {
                                    "cpu": "10m",
                                    "memory": "20Mi",
                                },
                                "limits": {
                                    "cpu": "20m",
                                    "memory": "50Mi",
                                }
                            }
                        }
                    ]
                }
            }
        }
    }
    logger.info("Patching metrics-server-nanny with lower resource requests/limits")
    patch_deployment(name='metrics-server-v0.3.1', patch=patch)


def patch_deployment(name: str, patch: str):
    api_instance = client.AppsV1Api()
    try:
        api_instance.patch_namespaced_deployment(
            name=name,
            namespace='kube-system',
            force=True,
            field_manager='right-sizer',
            body=patch)
    except client.rest.ApiException as e:
        logger.error(f"Failed to patch deployment: {name} - error was {e}")


def does_vpa_exist(obj_api, namespace, name) -> bool:

    try:
        obj_api.get_namespaced_custom_object(
            "autoscaling.k8s.io",
            "v1beta2",
            namespace,
            "verticalpodautoscalers",
            name)
        return True

    except client.rest.ApiException as e:
        if e.status == 404:
            return False
        else:
            raise
            return False


def generate_vpa_policy(obj, update_mode):

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


def create_vpa(obj_api, obj, update_mode):

    vpa = generate_vpa_policy(obj, update_mode)

    try:
        obj_api.create_namespaced_custom_object(
            "autoscaling.k8s.io",
            "v1beta2",
            obj.metadata.namespace,
            "verticalpodautoscalers",
            vpa)

    except client.rest.ApiException as e:
        logger.error(f"Failed to create VPA policy for {obj.metadata.namespace}/{obj.metadata.name} - error was {e}")


def init():

    if __name__ == "__main__":
        sys.exit(main())


init()
