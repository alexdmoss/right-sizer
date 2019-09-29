import logging
from kubernetes import client
from os import getenv

logging.basicConfig(level=logging.INFO,
                    format="-> [%(levelname)s] [%(asctime)s] %(message)s",
                    datefmt="%Y-%m-%d %H:%M")

logger = logging.getLogger(__name__)

if getenv("DEBUG"):
    logging.getLogger().setLevel(logging.DEBUG)
    logger.debug("Debugging is enabled")


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
