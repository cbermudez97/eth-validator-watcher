"""Contains the logic to check if the validators missed attestations."""

import functools

from prometheus_client import Gauge

from eth_validator_watcher.models import BeaconType

from .beacon import Beacon
from .messengers import Messenger
from .models import Validators
from .utils import LimitedDict

print = functools.partial(print, flush=True)

metric_missed_attestations_count = Gauge(
    "missed_attestations_count",
    "Missed attestations count",
)

metric_double_missed_attestations_count = Gauge(
    "double_missed_attestations_count",
    "Double missed attestations count",
)


def process_missed_attestations(
    beacon: Beacon,
    beacon_type: BeaconType,
    epoch_to_index_to_validator_index: LimitedDict,
    epoch: int,
) -> set[int]:
    """Process missed attestations.

    Parameters:
    beacon                       : Beacon instance
    beacon_type                  : Beacon type
    epoch_to_index_to_validator : Limited dictionary with:
        outer key             : epoch
        outer value, inner key: validator indexes
        inner value           : validators
    epoch                        : Epoch where the missed attestations are checked
    """
    if epoch < 1:
        return set()

    index_to_validator: dict[int, Validators.DataItem.Validator] = (
        epoch_to_index_to_validator_index[epoch - 1]
        if epoch - 1 in epoch_to_index_to_validator_index
        else epoch_to_index_to_validator_index[epoch]
    )

    validators_index = set(index_to_validator)
    validators_liveness = beacon.get_validators_liveness(
        beacon_type, epoch - 1, validators_index
    )

    dead_indexes = {
        index for index, liveness in validators_liveness.items() if not liveness
    }

    metric_missed_attestations_count.set(len(dead_indexes))

    if len(dead_indexes) == 0:
        return set()

    first_indexes = list(dead_indexes)[:5]

    first_pubkeys = (
        index_to_validator[first_index].pubkey for first_index in first_indexes
    )

    short_first_pubkeys = [pubkey[:10] for pubkey in first_pubkeys]
    short_first_pubkeys_str = ", ".join(short_first_pubkeys)

    print(
        f"🙁 Our validator {short_first_pubkeys_str} and "
        f"{len(dead_indexes) - len(short_first_pubkeys)} more "
        f"missed attestation at epoch {epoch - 1}"
    )

    return dead_indexes


def process_double_missed_attestations(
    dead_indexes: set[int],
    previous_dead_indexes: set[int],
    epoch_to_index_to_validator_index: LimitedDict,
    epoch: int,
    messenger: Messenger | None,
    explorer_url: str | None = None,
) -> set[int]:
    """Process double missed attestations.

    Parameters:
    dead_indexes               : Set of indexes of the validators that missed
                                attestations
    previous_dead_indexes      : Set of indexes of the validators that missed
                                attestations in the previous epoch

    epoch_to_index_to_validator: Limited dictionary with:
        outer key              : epoch
        outer value, inner key : validator indexes
        inner value            : validators

    epoch                      : Epoch where the missed attestations are checked
    messenger                  : Messenger instance
    explorer_url               : Beacon explorer URL
    """
    if epoch < 2:
        return set()

    double_dead_indexes = dead_indexes & previous_dead_indexes
    metric_double_missed_attestations_count.set(len(double_dead_indexes))

    if len(double_dead_indexes) == 0:
        return set()

    index_to_validator = epoch_to_index_to_validator_index[epoch - 1]
    first_indexes = list(double_dead_indexes)[:5]

    first_pubkeys = (
        index_to_validator[first_index].pubkey for first_index in first_indexes
    )

    short_first_pubkeys = [pubkey[:10] for pubkey in first_pubkeys]
    short_first_pubkeys_str = ", ".join(short_first_pubkeys)

    message_console = (
        f"😱 Our validator {short_first_pubkeys_str} and "
        f"{len(double_dead_indexes) - len(short_first_pubkeys)} more "
        f"missed 2 attestations in a row from epoch {epoch - 2}"
    )

    print(message_console)

    if messenger is not None:
        proposer_pubkey_link = f"`{short_first_pubkeys_str}`"
        epoch_link = f"`{epoch - 2}`"
        if explorer_url:
            proposer_pubkey_link = ", ".join(
                [
                    f"[{index_to_validator[proposer_index].pubkey[:10]}]({explorer_url}/validator/{index_to_validator[proposer_index].pubkey})"
                    for proposer_index in double_dead_indexes
                ]
            )
            epoch_link = f"[{epoch - 2}]({explorer_url}/epoch/{epoch - 2})"
        formatted_message = (
            f"😱 Our validator {proposer_pubkey_link} and "
            f"`{len(double_dead_indexes) - len(short_first_pubkeys)}` more "
            f"missed 2 attestations in a row from epoch {epoch_link}"
        )

        messenger.send_message(formatted_message)

    return double_dead_indexes
