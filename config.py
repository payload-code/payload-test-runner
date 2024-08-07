import os

CONFIG_FILE = "config.json"

DOCKER_COMPOSE_CMD = os.environ.get('DOCKER_COMPOSE_CMD', 'docker-compose')

REBUILD_DB_BEFORE_TESTS = os.environ.get('REBUILD_DB_BEFORE_TESTS', 'false').lower() == 'true'
YARN_REBUNDLE_BEFORE_TESTS = os.environ.get('YARN_REBUNDLE_BEFORE_TESTS', 'false').lower() == 'true'
