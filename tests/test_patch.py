import logging
from right_sizer import patch

logger = logging.getLogger(__name__)


def test_generate_patch():
    payload = patch.generate_patch(container="my-container",
                                   request_cpu="100m",
                                   limit_cpu="200m",
                                   request_memory="3Gi",
                                   limit_memory="4Gi")
    assert payload["spec"]["template"]["spec"]["containers"][0]["name"] == "my-container"
    assert payload["spec"]["template"]["spec"]["containers"][0]["resources"]["requests"]["cpu"] == "100m"
    assert payload["spec"]["template"]["spec"]["containers"][0]["resources"]["limits"]["cpu"] == "200m"
    assert payload["spec"]["template"]["spec"]["containers"][0]["resources"]["requests"]["memory"] == "3Gi"
    assert payload["spec"]["template"]["spec"]["containers"][0]["resources"]["limits"]["memory"] == "4Gi"


# def test_patch_kube_system_resources(mocker):
#     mocker.patch('right_sizer.patch.patch_deployment')
#     patch.patch_kube_system_resources()
#     assert patch.

# test_read_yaml
# (needs stub call) test_patch_deployment
