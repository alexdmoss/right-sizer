# right-sizer

Kubernetes Controller to create VPA (VerticalPodAutoscaler) policies on deployments within the cluster.

---

## Usage

You need either `docker` or `python` on your local machine - both are easy to install on most common OSes.

If using python directly, `pipenv install --dev` from the root directory.

There is a wrapper script (`./go` in `bash`) to make this easier (**Note:** CI does not currently use this):

- `./go run`- run go locally without building
- `./go test` - run unit tests and benchmarks
- `./go build` - builds docker image locally and runs smoke tests

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

- [x] Controller to create VPA policy for all workloads
- [x] Configuration option to allow recommend/update
- [x] Configuration option to target specific namespace
- [x] Docker packaging
- [x] Deployment to cluster
- [x] CI
- [ ] Need to add image versioning to CI deployment
- [ ] Clean up patching code if it proves to be viable
- [ ] Tests
- [ ] Extend to cover DaemonSets & StatefulSets?
