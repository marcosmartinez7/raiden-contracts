import pytest
from eth_tester.exceptions import TransactionFailed

from raiden_contracts.constants import CONTRACTS_VERSION
from raiden_contracts.utils.proofs import sign_one_to_n_iou


def test_claim(
    user_deposit_contract,
    one_to_n_contract,
    custom_token,
    get_accounts,
    get_private_key,
    web3,
):
    user_deposit_contract.functions.init(one_to_n_contract.address).transact()
    (A, B) = get_accounts(2)
    custom_token.functions.mint(30).transact({'from': A})
    custom_token.functions.approve(user_deposit_contract.address, 30).transact({'from': A})
    user_deposit_contract.functions.deposit(A, 30).transact({'from': A})

    # happy case
    amount = 10
    expiration = web3.eth.blockNumber + 2
    signature = sign_one_to_n_iou(
        get_private_key(A),
        sender=A,
        receiver=B,
        amount=amount,
        expiration=expiration,
    )
    one_to_n_contract.functions.claim(
        A, B, amount, expiration, signature,
    ).transact({'from': A})

    assert user_deposit_contract.functions.balances(A).call() == 20
    assert user_deposit_contract.functions.balances(B).call() == 10

    # can't be claimed twice
    with pytest.raises(TransactionFailed):
        one_to_n_contract.functions.claim(
            A, B, amount, expiration, signature,
        ).transact({'from': A})

    # IOU expired
    with pytest.raises(TransactionFailed):
        bad_expiration = web3.eth.blockNumber
        signature = sign_one_to_n_iou(
            get_private_key(A),
            sender=A,
            receiver=B,
            amount=amount,
            expiration=bad_expiration,
        )
        one_to_n_contract.functions.claim(
            A, B, amount, bad_expiration, signature,
        ).transact({'from': A})

    # bad signature
    with pytest.raises(TransactionFailed):
        expiration = web3.eth.blockNumber + 1
        signature = sign_one_to_n_iou(
            get_private_key(A),
            sender=A,
            receiver=B,
            amount=amount + 1,  # this does not match amount below
            expiration=expiration,
        )
        one_to_n_contract.functions.claim(
            A, B, amount, expiration, signature,
        ).transact({'from': A})


def test_claim_with_insufficient_deposit(
    user_deposit_contract,
    one_to_n_contract,
    custom_token,
    get_accounts,
    get_private_key,
    web3,
):
    user_deposit_contract.functions.init(one_to_n_contract.address).transact()
    (A, B) = get_accounts(2)
    custom_token.functions.mint(10).transact({'from': A})
    custom_token.functions.approve(user_deposit_contract.address, 10).transact({'from': A})
    user_deposit_contract.functions.deposit(A, 6).transact({'from': A})

    amount = 10
    expiration = web3.eth.blockNumber + 1
    signature = sign_one_to_n_iou(
        get_private_key(A),
        sender=A,
        receiver=B,
        amount=amount,
        expiration=expiration,
    )

    # amount is 10, but only 6 are in deposit
    # check return value (transactions don't give back return values, so use call)
    assert one_to_n_contract.functions.claim(
        A, B, amount, expiration, signature,
    ).call({'from': A}) == 6
    # check that transaction succeeds
    one_to_n_contract.functions.claim(
        A, B, amount, expiration, signature,
    ).transact({'from': A})

    assert user_deposit_contract.functions.balances(A).call() == 0
    assert user_deposit_contract.functions.balances(B).call() == 6

    # claim can be retried when transferred amount was 0
    expiration = web3.eth.blockNumber + 3
    signature = sign_one_to_n_iou(
        get_private_key(A),
        sender=A,
        receiver=B,
        amount=amount,
        expiration=expiration,
    )
    one_to_n_contract.functions.claim(
        A, B, amount, expiration, signature,
    ).transact({'from': A})
    user_deposit_contract.functions.deposit(A, 6 + 4).transact({'from': A})
    one_to_n_contract.functions.claim(
        A, B, amount, expiration, signature,
    ).transact({'from': A})


def test_version(one_to_n_contract):
    """ Check the result of contract_version() call on the UserDeposit """
    version = one_to_n_contract.functions.contract_version().call()
    assert version == CONTRACTS_VERSION
