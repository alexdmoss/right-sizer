import yaml
import logging
from os import getenv
from kubernetes import client

logging.basicConfig(level=logging.INFO,
                    format="-> [%(levelname)s] [%(asctime)s] %(message)s",
                    datefmt="%Y-%m-%d %H:%M")

logger = logging.getLogger(__name__)

if getenv("DEBUG"):
    logging.getLogger().setLevel(logging.DEBUG)
    logger.debug("Debugging is enabled")


def patch_kube_system_resources():

    patch_file = "patch-kube-system-resources.yaml"

    for deployment, containers in yaml.load(open(patch_file), Loader=yaml.FullLoader)["deployments"].items():

        for container, resources in containers.items():

            patch = generate_patch(container=container,
                                   request_cpu=resources["requests"]["cpu"],
                                   request_memory=resources["requests"]["memory"],
                                   limit_cpu=resources["limits"]["cpu"],
                                   limit_memory=resources["limits"]["memory"])

            logger.info(f"Patching {deployment}:{container} with lower resource requests/limits")

            patch_deployment(name=deployment, patch=patch)


def generate_patch(container, request_cpu, request_memory, limit_cpu, limit_memory):

    patch = {
                "spec": {
                    "template": {
                        "spec": {
                            "containers": [
                                {
                                    "name": container,
                                    "resources": {
                                        "requests": {
                                            "cpu": request_cpu,
                                            "memory": request_memory,
                                        },
                                        "limits": {
                                            "cpu": limit_cpu,
                                            "memory": limit_memory,
                                        }
                                    }
                                }
                            ]
                        }
                    }
                }
            }

    logger.debug(f"Generated Patch Object: {patch}")

    return patch


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
