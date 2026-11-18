import pytest

from costassist.knowledge import load_knowledge
from costassist.scenarios import build_scenario


@pytest.fixture(scope="session")
def chunks():
    return load_knowledge()


@pytest.fixture(scope="session")
def scenario_lambda():
    return build_scenario(6)  # S07 lambda_recursive_loop, team data-platform


@pytest.fixture(scope="session")
def scenario_nat():
    return build_scenario(0)  # S01 nat_gateway_data_processing, team payments
