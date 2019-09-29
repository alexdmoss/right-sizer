import logging
from os import getenv

logging.basicConfig(level=logging.INFO,
                    format="-> [%(levelname)s] [%(asctime)s] %(message)s",
                    datefmt="%Y-%m-%d %H:%M")

logger = logging.getLogger(__name__)


def set_update_mode():
    if getenv("UPDATE_MODE") == 'Auto':
        logger.info("Running in UPDATE mode - pods will be set to resize automatically")
        return "Auto"
    else:
        logger.info("Running in RECOMMEND mode (default) - pods will not be auto-resized")
        return "Off"


def set_namespace():
    target_namespace = getenv("NAMESPACE")
    if target_namespace:
        logger.info(f"Namespace specified - VPA policy will only be created for deployments in {target_namespace}")
        return target_namespace
    else:
        logger.info("No namespace specified - ALL namespaces will be targeted with VPA policy")
        return False


def set_patch_kube_system():
    patch = getenv("PATCH_KUBE_SYSTEM")
    if patch == "True":
        logger.info(f"Patching of kube-system is ENABLED - kube-system resources will have resource requests/limits updated")
        return True
    else:
        logger.info("Patching of kube-system is DISABLED - these will be managed by Kubernetes itself")
        return False


def set_update_frequency():
    freq = getenv("UPDATE_FREQUENCY")
    if freq:
        logger.info(f"Controller will run every {freq} seconds")
        return int(freq)
    else:
        logger.info(f"Controller will run every 600 seconds (default)")
        return 600
