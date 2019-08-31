# right-sizer

Kubernetes Controller to create VPA (VerticalPodAutoscaler) policies and other resource request/limit settings on resources within the cluster.

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

## To Do

- [ ] Controller to create VPA policy for all workloads
- [ ] Controller to set resource requests/limits on certain objects
- [ ] Tests
- [ ] CI
