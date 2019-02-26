import pytest
from raiden_contracts.constants import (
    CONTRACT_HUMAN_STANDARD_TOKEN,
    CONTRACT_CUSTOM_TOKEN,
)

token_args = (10 ** 26, 18, CONTRACT_CUSTOM_TOKEN, 'TKN')


@pytest.fixture(scope='session')
def custom_token_factory(deploy_tester_contract):
    """A function that deploys a CustomToken contract"""
    def f():
        return deploy_tester_contract(
            CONTRACT_CUSTOM_TOKEN,
            [],
            token_args,
        )
    return f


@pytest.fixture(scope='session')
def custom_token(custom_token_factory):
    """Deploy CustomToken contract"""
    return custom_token_factory()


@pytest.fixture()
def human_standard_token(deploy_token_contract):
    """Deploy HumanStandardToken contract"""
    return deploy_token_contract(*token_args)


@pytest.fixture
def deploy_token_contract(deploy_tester_contract):
    """Returns a function that deploys a generic HumanStandardToken contract"""
    def f(initial_amount: int, decimals: int, token_name: str, token_symbol: str):
        assert initial_amount > 0
        assert decimals > 0
        return deploy_tester_contract(
            CONTRACT_HUMAN_STANDARD_TOKEN,
            [],
            [initial_amount, decimals, token_name, token_symbol],
        )

    return f


@pytest.fixture
def standard_token_contract(custom_token):
    """Deployed CustomToken contract"""
    return custom_token
