from scalecodec import ss58_encode

from async_substrate_interface.sync_substrate import SubstrateInterface
from async_substrate_interface.types import ScaleObj
from tests.helpers.settings import ARCHIVE_ENTRYPOINT, LATENT_LITE_ENTRYPOINT


def test_legacy_decoding():
    # roughly 4000 blocks before metadata v15 was added
    pre_metadata_v15_block = 3_010_611

    with SubstrateInterface(ARCHIVE_ENTRYPOINT) as substrate:
        block_hash = substrate.get_block_hash(pre_metadata_v15_block)
        events = substrate.get_events(block_hash)
        assert isinstance(events, list)

        query_map_result = substrate.query_map(
            module="SubtensorModule",
            storage_function="NetworksAdded",
            block_hash=block_hash,
        )
        for key, value in query_map_result:
            assert isinstance(key, int)
            assert isinstance(value, ScaleObj)

        timestamp = substrate.query(
            "Timestamp",
            "Now",
            block_hash=block_hash,
        )
        assert timestamp.value == 1716358476004


def test_ss58_conversion():
    with SubstrateInterface(
        LATENT_LITE_ENTRYPOINT, ss58_format=42, decode_ss58=False
    ) as substrate:
        block_hash = substrate.get_chain_finalised_head()
        qm = substrate.query_map(
            "SubtensorModule",
            "OwnedHotkeys",
            block_hash=block_hash,
        )
        # only do the first page, bc otherwise this will be massive
        for key, value in qm.records:
            assert isinstance(key, tuple)
            assert isinstance(value, ScaleObj)
            assert isinstance(value.value, list)
            assert len(key) == 1
            for key_tuple in value.value:
                assert len(key_tuple[0]) == 32
                random_key = key_tuple[0]

        ss58_of_key = ss58_encode(bytes(random_key), substrate.ss58_format)
        assert isinstance(ss58_of_key, str)

        substrate.decode_ss58 = True  # change to decoding True

        qm = substrate.query_map(
            "SubtensorModule",
            "OwnedHotkeys",
            block_hash=block_hash,
        )
        for key, value in qm.records:
            assert isinstance(key, str)
            assert isinstance(value, ScaleObj)
            assert isinstance(value.value, list)
            if len(value.value) > 0:
                for decoded_key in value.value:
                    assert isinstance(decoded_key, str)
