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

## Setting Caps

The code can be updated to set caps if you wish, add this to `generate_vpa_policy`'s spec (under `updatePolicy`):

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
- [ ] Docker packaging
- [ ] Deployment to cluster
- [ ] CI
- [ ] Tests
- [ ] Controller to set resource requests/limits on certain objects - e.g. individual pods?
- [ ] Extend to cover DaemonSets & StatefulSets?
