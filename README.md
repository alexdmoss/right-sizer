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
- `./go build` - builds docker image locally, which includes running the tests baked into the Dockerfile
- `./go deploy` - typically run in a CI pipeline. Applies Kubernetes yaml to deploy the built image (which has been pushed by a previous CI stage)

NB: You can use `pipenv run ptw` to continuously run your tests in the background - quite helpful!

---

## Patching Deployments & DaemonSets in kube-system

Some fun and games with this. The following seem to be on the more resource-hungry side:

- Deployments:
  - heapster-v1.6.1 - wants a lot of memory
  - kube-dns - wants a lot of CPU
- DaemonSets:
  - fluentd-gcp-v3.1.1 - wants a lot of memory
- Pods:
  - kube-proxy - wants a lot of CPU

We can patch the Deployments using our Controller - the code currently is horrendous as I just wanted to prove this works - I'm leaving the controller running for a bit to prove this out before I'll come back and tidy this up!

The Fluentd DaemonSet can be easily scaled via the ScalingPolicy - see "How to create a custom scaling policy" under https://cloud.google.com/kubernetes-engine/docs/how-to/small-cluster-tuning#logging. Mine is as follows:
disable HPA (addon)

```yaml
---
apiVersion: scalingpolicy.kope.io/v1alpha1
kind: ScalingPolicy
metadata:
  name: fluentd-gcp-scaling-policy
  namespace: kube-system
spec:
  containers:
  - name: fluentd-gcp
    resources:
      limits:
      - base: 50m
        resource: cpu
      - base: 200Mi
        resource: memory
      requests:
      - base: 10m
        resource: cpu
      - base: 50Mi
        resource: memory
```

However, `kube-proxy` sucks because it is a set of bare pods that *look* like a DaemonSet but there ain't no DaemonSet to configure - presumably it sits on the GKE Master node(s) which we can't reach. This means that, as far as I can tell, we need to live with the lack of limits set here, as VPA can't manage bare pods either and you can't patch the resource requests/limits of a Pod. Boo hiss.

Experimenting with this looks a little like this:

```sh
kubectl patch deployment kube-dns -p '{"spec": {"template": {"spec": {"containers": [{"name":"kubedns","resources":{"limits":{"cpu":"20m","memory":"100Mi"},"requests":{"cpu":"10m","memory":"50Mi"}}}]}}}}'
```

---

## Setting Caps For the VPA

**If** you go with `updateMode: Auto` then it is probably a smart idea to update the code to set some caps. The extension to the spec is below, but keep in mind this would get applied to **all** your Deployments - add this to `generate_vpa_policy`'s spec (under `updatePolicy`):

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

- [ ] Add fluentd GCP scaler
- [ ] Clean up patching code if it proves to be viable
- [ ] Can we scan for matching deployments to avoid the hardcoded version issue?
- [ ] Tests
- [ ] Extend to cover DaemonSets & StatefulSets?
