"""Contains functions to handle missed block proposals detection on head"""

import functools

from prometheus_client import Counter

from .beacon import Beacon, NoBlockError
from .messengers import Messenger
from .models import Block, BlockIdentierType
from .utils import NB_SLOT_PER_EPOCH

print = functools.partial(print, flush=True)

metric_missed_block_proposals_head_count = Counter(
    "missed_block_proposals_head_count",
    "Missed block proposals head count",
)

metric_missed_block_proposals_finalized_count = Counter(
    "missed_block_proposals_finalized_count",
    "Missed block proposals finalized count",
)


def process_missed_blocks_head(
    beacon: Beacon,
    potential_block: Block | None,
    slot: int,
    our_pubkeys: set[str],
    messenger: Messenger | None,
    slots_per_epoch: int = NB_SLOT_PER_EPOCH,
    explorer_url: str | None = None,
) -> bool:
    """Process missed block proposals detection at head

    Parameters:
    beacon         : Beacon
    potential_block: Potential block
    slot           : Slot
    our_pubkeys    : Set of our validators public keys
    messenger      : Messenger instance
    slots_per_epoch: Slots per epoch
    explorer_url   : Beacon Explorer URL

    Returns `True` if we had to propose the block, `False` otherwise
    """
    missed = potential_block is None
    epoch = slot // slots_per_epoch
    proposer_duties = beacon.get_proposer_duties(epoch)

    # Get proposer public key for this slot
    proposer_duties_data = proposer_duties.data

    # In `data` list, items seem to be ordered by slot.
    # However, there is no specification for that, so it is wiser to
    # iterate on the list
    proposer_pubkey = next(
        (
            proposer_duty_data.pubkey
            for proposer_duty_data in proposer_duties_data
            if proposer_duty_data.slot == slot
        )
    )

    # Check if the validator that has to propose is ours
    is_our_validator = proposer_pubkey in our_pubkeys
    positive_emoji = "✨" if is_our_validator else "✅"
    negative_emoji = "🔺" if is_our_validator else "💩"

    emoji, proposed_or_missed = (
        (negative_emoji, "missed  ") if missed else (positive_emoji, "proposed")
    )

    short_proposer_pubkey = proposer_pubkey[:10]

    message_console = (
        f"{emoji} {'Our ' if is_our_validator else '    '}validator "
        f"{short_proposer_pubkey} {proposed_or_missed} block at head at epoch {epoch} "
        f"- slot {slot} {emoji} - 🔑 {len(our_pubkeys)} keys "
        "watched"
    )

    print(message_console)

    if messenger is not None and missed and is_our_validator:
        proposer_pubkey_link = f"`{short_proposer_pubkey}`"
        epoch_link = f"`{epoch}`"
        slot_link = f"`{slot}`"
        if explorer_url:
            proposer_pubkey_link = (
                f"[{short_proposer_pubkey}]({explorer_url}/validator/{proposer_pubkey})"
            )
            epoch_link = f"[{epoch}]({explorer_url}/epoch/{epoch})"
            slot_link = f"[{slot}]({explorer_url}/slot/{slot})"

        formatted_message = (
            f"{emoji} {'Our ' if is_our_validator else '    '}validator "
            f"{proposer_pubkey_link} {proposed_or_missed} block at head at epoch "
            f"{epoch_link} - slot {slot_link} {emoji}"
        )

        messenger.send_message(formatted_message)

    if is_our_validator and missed:
        metric_missed_block_proposals_head_count.inc()

    return is_our_validator


def process_missed_blocks_finalized(
    beacon: Beacon,
    last_processed_finalized_slot: int,
    slot: int,
    our_pubkeys: set[str],
    messenger: Messenger | None,
    slots_per_epoch: int = NB_SLOT_PER_EPOCH,
    explorer_url: str | None = None,
) -> int:
    """Process missed block proposals detection at finalized

    Parameters:
    beacon         : Beacon
    potential_block: Potential block
    slot           : Slot
    our_pubkeys    : Set of our validators public keys
    messenger      : Messenger instance
    slots_per_epoch: Slots per epoch
    explorer_url   : Beacon Explorer URL

    Returns the last finalized slot
    """
    assert last_processed_finalized_slot <= slot, "Last processed finalized slot > slot"

    last_finalized_header = beacon.get_header(BlockIdentierType.FINALIZED)
    last_finalized_slot = last_finalized_header.data.header.message.slot
    epoch_of_last_finalized_slot = last_finalized_slot // slots_per_epoch

    # Only to memoize it, in case of the BN does not serve this request for too old
    # epochs
    beacon.get_proposer_duties(epoch_of_last_finalized_slot)

    for slot_ in range(last_processed_finalized_slot + 1, last_finalized_slot + 1):
        epoch = slot_ // slots_per_epoch
        proposer_duties = beacon.get_proposer_duties(epoch)

        # Get proposer public key for this slot
        proposer_duties_data = proposer_duties.data

        # In `data` list, items seem to be ordered by slot.
        # However, there is no specification for that, so it is wiser to
        # iterate on the list
        proposer_pubkey = next(
            (
                proposer_duty_data.pubkey
                for proposer_duty_data in proposer_duties_data
                if proposer_duty_data.slot == slot_
            )
        )

        # Check if the validator that has to propose is ours
        is_our_validator = proposer_pubkey in our_pubkeys

        if not is_our_validator:
            continue

        # Check if the block has been proposed
        try:
            beacon.get_header(slot_)
        except NoBlockError:
            short_proposer_pubkey = proposer_pubkey[:10]

            message_console = (
                f"❌ Our validator {short_proposer_pubkey} missed block at finalized "
                f"at epoch {epoch} - slot {slot_} ❌"
            )

            print(message_console)

            if messenger is not None:
                proposer_pubkey_link = f"`{short_proposer_pubkey}`"
                epoch_link = f"`{epoch}`"
                slot_link = f"`{slot_}`"
                if explorer_url:
                    proposer_pubkey_link = f"[{short_proposer_pubkey}]({explorer_url}/validator/{proposer_pubkey})"
                    epoch_link = f"[{epoch}]({explorer_url}/epoch/{epoch})"
                    slot_link = f"[{slot_}]({explorer_url}/slot/{slot_})"
                formatted_message = (
                    f"❌ Our validator {proposer_pubkey_link} missed block at "
                    f"finalized at epoch {epoch_link} - slot {slot_link} ❌"
                )

                messenger.send_message(formatted_message)

            metric_missed_block_proposals_finalized_count.inc()

    return last_finalized_slot
