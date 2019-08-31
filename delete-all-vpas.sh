#!/usr/bin/env bash

if [[ $(kubectl get vpa | wc -l) -gt 0 ]]; then
    kubectl get vpa --all-namespaces -o=jsonpath="{range .items[*]}{.metadata.name} {.metadata.namespace}{'\n'}{end}" | xargs -n 2 sh -c 'kubectl delete vpa $0 -n=$1'
fi

echo; echo "Confirming all deleted:"; echo

kubectl get vpa --all-namespaces