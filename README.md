# right-sizer

Kubernetes Controller to create VPA (VerticalPodAutoscaler) policies on deployments within the cluster.

I've written more about this in a blog post here: https://mosstech.io/2019/09/28/squeezing-gke-system-resources-in-small-clusters/

---

## What Does It Do

It is a custom controller written in Python.

### 1. Create VPA Policy

It will watch for new Deployments being created (either in all namespaces or a particular one, depending on supplied argument) and create a corresponding VPA resource in either "recommend mode" or update mode. See `./k8s/right-sizer.yaml` (in particular, the comments) for configuring this behaviour.

### 2. Patch kube-system Pods

When `KUBE_PATCH_SYSTEM` is set to True, it will also target particular resources in the `kube-system` namespace for patching - since we do not control the PodSpec for these.

This effectively re-applies chosen resource requests/limits for named pods every 10 minutes - overriding any settings applied by Google for these GKE-managed resources. **Use this feature at your own risk!**

### 3. Apply Fluentd GCP ScalingPolicy

Finally, the deployment stage of the CI will apply `./k8s/fluentd-scaling.yaml`, which creates a `ScalingPolicy` for GKE's `fluentd-gcp-auto-scaler` to use to right-size Fluentd. This is a built-in feature of GKE, so skipped by the patching above.

---

## Development

I like using a `go` bash wrapper script because I am lazy.

- `./go init` effectively runs `.pipenv install --dev` from the root directory as a one-off to get started with this repo
- `./go run`- runs the controller locally without building
- `./go test` - runs lint and pytest locally
- `./go watch-tests` - runs pytest continuously in the background (using the `ptw` module)
- `./go build` - builds docker image locally, which includes running the tests baked into the Dockerfile
- `./go deploy` - typically run in a CI pipeline. Applies Kubernetes yaml to deploy the built image (which has been pushed by a previous CI stage)

---

## Patching Deployments & DaemonSets in kube-system

Values to patch into the kube-system deployments are stored in a fairly self-intuitive yaml file `./patch-kube-system-resources.yaml`. Names must match exactly the resources in kube-system you want to patch: deployment -> container -> limits|requests -> cpu|memory.

I chose to patch kube-dns, heapster and metrics-server, as these were the beefiest in my current GKE setup. I wanted  patch `kube-proxy`, but it sucks because it is a set of bare pods that *look* like a DaemonSet but there ain't no DaemonSet to configure - presumably it sits on the GKE Master node(s) which we can't reach. This means that, as far as I can tell, we need to live with the lack of limits set here, as VPA can't manage bare pods either and you can't patch the resource requests/limits of a Pod (the PodSpec is immutable). Boo hiss.

As noted above, Fluentd DaemonSet is handled separately as it can be easily scaled via the ScalingPolicy - see "How to create a custom scaling policy" under https://cloud.google.com/kubernetes-engine/docs/how-to/small-cluster-tuning#logging.

---

## Setting Caps For the VPA

**If** you go with `updateMode: Auto` (I didn't) then it is probably a smart idea to update the code to set some caps. The extension to the spec is below, but keep in mind this would get applied to **all** your Deployments - add this to `generate_vpa_policy`'s spec (under `updatePolicy`):

```python
"resourcePolicy": {
    "containerPolicies": [
        {
            "containerName": "*",
            "maxAllowed": {
                "memory": "200Mi",
                "cpu": "200m",
            },
            "minAllowed": {
                "memory": "50Mi",
                "cpu": "10m",
            }
        }
    ]
}
```

---

## To Do

- [ ] Can we scan for matching deployments to avoid the hardcoded version issue?
- [ ] Tests
- [ ] Extend to cover DaemonSets & StatefulSets? *I do not have a need currently*
