#!/usr/bin/env bash
set -euo pipefail

if [[ -z ${IMAGE_NAME:-} ]]; then
  IMAGE_NAME=right-sizer
fi 

# set to N if you want linting failures to stop ./go test
ignore_linting_failures=Y

function help() {
  echo -e "Usage: go <command>"
  echo -e
  echo -e "    help               Print this help"
  echo -e "    run                Run locally without building binary"
  echo -e "    build              Build binary locally"
  echo -e "    test               Run local unit tests and linting"
  echo -e "    init               Set up local virtual env"
  echo -e 
  exit 0
}

function init() {

  _console_msg "Initialising local virtual environment ..." INFO true

  pipenv install --dev

  _console_msg "Init complete" INFO true

}

function run() {

  _console_msg "Running python:main ..." INFO true

  pipenv run python3 main.py

  _console_msg "Execution complete" INFO true

}

function test() {

    _console_msg "Running pylint ..." INFO true

    if [[ ${ignore_linting_failures} == "Y" ]]; then

      pipenv run pylint main.py  || true
      pipenv run pylint modules/ || true

      _console_msg "Running flake8 ..." INFO true

      pipenv run flake8 main.py  || true
      pipenv run flake8 modules/ || true

      _console_msg "Running pycodestyle (pep8) ..." INFO true

      pipenv run pycodestyle main.py  || true
      pipenv run pycodestyle modules/ || true

    else 
      
      pipenv run pylint main.py
      pipenv run pylint modules/

      _console_msg "Running flake8 ..." INFO true

      pipenv run flake8 main.py
      pipenv run flake8 modules/

      _console_msg "Running pycodestyle (pep8) ..." INFO true

      pipenv run pycodestyle main.py 
      pipenv run pycodestyle modules/
    
    fi 

    _console_msg "Running unit tests ..." INFO true

    # pip install pipenv==2018.10.13
    # pipenv install --dev --deploy --ignore-pipfile --system
    # pipenv run pytest -s -v "./test_main.py" --disable-pytest-warnings --junit-xml junit-report.xml  
    # pipenv lock -r > requirements.txt

    _console_msg "Tests complete" INFO true

}

function build() {

  _console_msg "Building python docker image ..." INFO true

  docker build -t ${IMAGE_NAME} .

  _console_msg "Build complete" INFO true

}

function _assert_variables_set() {

  local error=0
  local varname
  
  for varname in "$@"; do
    if [[ -z "${!varname-}" ]]; then
      echo "${varname} must be set" >&2
      error=1
    fi
  done
  
  if [[ ${error} = 1 ]]; then
    exit 1
  fi

}

function _console_msg() {

  local msg=${1}
  local level=${2:-}
  local ts=${3:-}

  if [[ -z ${level} ]]; then level=INFO; fi
  if [[ -n ${ts} ]]; then ts=" [$(date +"%Y-%m-%d %H:%M")]"; fi

  echo ""

  if [[ ${level} == "ERROR" ]] || [[ ${level} == "CRIT" ]] || [[ ${level} == "FATAL" ]]; then
    (echo 2>&1)
    (echo >&2 "-> [${level}]${ts} ${msg}")
  else 
    (echo "-> [${level}]${ts} ${msg}")
  fi

  echo ""

}

function ctrl_c() {
    if [ ! -z ${PID:-} ]; then
        kill ${PID}
    fi
    exit 1
}

trap ctrl_c INT

if [[ ${1:-} =~ ^(help|run|build|test|init)$ ]]; then
  COMMAND=${1}
  shift
  $COMMAND "$@"
else
  help
  exit 1
fi
