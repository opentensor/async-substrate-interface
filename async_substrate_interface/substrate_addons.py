import asyncio
import logging
from functools import partial
from itertools import cycle
from typing import Optional, Type, Union

from async_substrate_interface.async_substrate import AsyncSubstrateInterface
from async_substrate_interface.errors import MaxRetriesExceeded
from async_substrate_interface.sync_substrate import SubstrateInterface

SubstrateClass = Type[Union[SubstrateInterface, AsyncSubstrateInterface]]


class RetrySubstrate:
    def __init__(
        self,
        substrate: SubstrateClass,
        main_url: str,
        use_remote_preset: bool = False,
        fallback_chains: Optional[list[str]] = None,
        retry_forever: bool = False,
        ss58_format: Optional[int] = None,
        type_registry: Optional[dict] = None,
        type_registry_preset: Optional[str] = None,
        chain_name: str = "",
        max_retries: int = 5,
        retry_timeout: float = 60.0,
        _mock: bool = False,
    ):
        fallback_chains = fallback_chains or []
        self._substrate_class: SubstrateClass = substrate
        self.ss58_format: int = ss58_format
        self.type_registry: dict = type_registry
        self.use_remote_preset: bool = use_remote_preset
        self.chain_name: Optional[str] = chain_name
        self.max_retries: int = max_retries
        self.retry_timeout: float = retry_timeout
        self._mock = _mock
        self.type_registry_preset: Optional[str] = type_registry_preset
        self.fallback_chains = (
            iter(fallback_chains)
            if not retry_forever
            else cycle(fallback_chains + [main_url])
        )
        initialized = False
        for chain_url in [main_url] + fallback_chains:
            try:
                self._substrate = self._substrate_class(
                    url=chain_url,
                    ss58_format=ss58_format,
                    type_registry=type_registry,
                    use_remote_preset=use_remote_preset,
                    chain_name=chain_name,
                    _mock=_mock,
                )
                initialized = True
                break
            except ConnectionError:
                logging.warning(f"Unable to connect to {chain_url}")
        if not initialized:
            raise ConnectionError(
                f"Unable to connect at any chains specified: {[main_url] + fallback_chains}"
            )

        # retries

        # TODO: properties that need retry logic
        # properties
        # version
        # token_decimals
        # token_symbol
        # name

        retry = (
            self._async_retry
            if self._substrate_class == AsyncSubstrateInterface
            else self._retry
        )

        self._get_block_handler = partial(retry, "_get_block_handler")
        self.apply_type_registry_presets = partial(retry, "apply_type_registry_presets")
        self.close = partial(retry, "close")
        self.compose_call = partial(retry, "compose_call")
        self.connect = partial(retry, "connect")
        self.create_scale_object = partial(retry, "create_scale_object")
        self.create_signed_extrinsic = partial(retry, "create_signed_extrinsic")
        self.create_storage_key = partial(retry, "create_storage_key")
        self.decode_scale = partial(retry, "decode_scale")
        self.encode_scale = partial(retry, "encode_scale")
        self.extension_call = partial(retry, "extension_call")
        self.filter_events = partial(retry, "filter_events")
        self.filter_extrinsics = partial(retry, "filter_extrinsics")
        self.generate_signature_payload = partial(retry, "generate_signature_payload")
        self.get_account_next_index = partial(retry, "get_account_next_index")
        self.get_account_nonce = partial(retry, "get_account_nonce")
        self.get_block = partial(retry, "get_block")
        self.get_block_hash = partial(retry, "get_block_hash")
        self.get_block_header = partial(retry, "get_block_header")
        self.get_block_metadata = partial(retry, "get_block_metadata")
        self.get_block_number = partial(retry, "get_block_number")
        self.get_block_runtime_info = partial(retry, "get_block_runtime_info")
        self.get_block_runtime_version_for = partial(
            retry, "get_block_runtime_version_for"
        )
        self.get_block_timestamp = partial(retry, "get_block_timestamp")
        self.get_chain_finalised_head = partial(retry, "get_chain_finalised_head")
        self.get_chain_head = partial(retry, "get_chain_head")
        self.get_constant = partial(retry, "get_constant")
        self.get_events = partial(retry, "get_events")
        self.get_extrinsics = partial(retry, "get_extrinsics")
        self.get_metadata_call_function = partial(retry, "get_metadata_call_function")
        self.get_metadata_constant = partial(retry, "get_metadata_constant")
        self.get_metadata_error = partial(retry, "get_metadata_error")
        self.get_metadata_errors = partial(retry, "get_metadata_errors")
        self.get_metadata_module = partial(retry, "get_metadata_module")
        self.get_metadata_modules = partial(retry, "get_metadata_modules")
        self.get_metadata_runtime_call_function = partial(
            retry, "get_metadata_runtime_call_function"
        )
        self.get_metadata_runtime_call_functions = partial(
            retry, "get_metadata_runtime_call_functions"
        )
        self.get_metadata_storage_function = partial(
            retry, "get_metadata_storage_function"
        )
        self.get_metadata_storage_functions = partial(
            retry, "get_metadata_storage_functions"
        )
        self.get_parent_block_hash = partial(retry, "get_parent_block_hash")
        self.get_payment_info = partial(retry, "get_payment_info")
        self.get_storage_item = partial(retry, "get_storage_item")
        self.get_type_definition = partial(retry, "get_type_definition")
        self.get_type_registry = partial(retry, "get_type_registry")
        self.init_runtime = partial(retry, "init_runtime")
        self.initialize = partial(retry, "initialize")
        self.is_valid_ss58_address = partial(retry, "is_valid_ss58_address")
        self.load_runtime = partial(retry, "load_runtime")
        self.make_payload = partial(retry, "make_payload")
        self.query = partial(retry, "query")
        self.query_map = partial(retry, "query_map")
        self.query_multi = partial(retry, "query_multi")
        self.query_multiple = partial(retry, "query_multiple")
        self.reload_type_registry = partial(retry, "reload_type_registry")
        self.retrieve_extrinsic_by_hash = partial(retry, "retrieve_extrinsic_by_hash")
        self.retrieve_extrinsic_by_identifier = partial(
            retry, "retrieve_extrinsic_by_identifier"
        )
        self.rpc_request = partial(retry, "rpc_request")
        self.runtime_call = partial(retry, "runtime_call")
        self.search_block_number = partial(retry, "search_block_number")
        self.serialize_constant = partial(retry, "serialize_constant")
        self.serialize_module_call = partial(retry, "serialize_module_call")
        self.serialize_module_error = partial(retry, "serialize_module_error")
        self.serialize_module_event = partial(retry, "serialize_module_event")
        self.serialize_storage_item = partial(retry, "serialize_storage_item")
        self.ss58_decode = partial(retry, "ss58_decode")
        self.ss58_encode = partial(retry, "ss58_encode")
        self.submit_extrinsic = partial(retry, "submit_extrinsic")
        self.subscribe_block_headers = partial(retry, "subscribe_block_headers")
        self.supports_rpc_method = partial(retry, "supports_rpc_method")
        self.ws = self._substrate.ws

    def _retry(self, method, *args, **kwargs):
        try:
            method_ = getattr(self._substrate, method)
            return method_(*args, **kwargs)
        except (MaxRetriesExceeded, ConnectionError, ConnectionRefusedError) as e:
            try:
                self._reinstantiate_substrate(e)
                method_ = getattr(self._substrate, method)
                return self._retry(method_(*args, **kwargs))
            except StopIteration:
                logging.error(
                    f"Max retries exceeded with {self._substrate.url}. No more fallback chains."
                )
                raise MaxRetriesExceeded

    async def _async_retry(self, method, *args, **kwargs):
        try:
            method_ = getattr(self._substrate, method)
            if asyncio.iscoroutinefunction(method_):
                return await method_(*args, **kwargs)
            else:
                return method_(*args, **kwargs)
        except (MaxRetriesExceeded, ConnectionError, ConnectionRefusedError) as e:
            try:
                self._reinstantiate_substrate(e)
                method_ = getattr(self._substrate, method)
                if asyncio.iscoroutinefunction(method_):
                    return await method_(*args, **kwargs)
                else:
                    return method_(*args, **kwargs)
            except StopIteration:
                logging.error(
                    f"Max retries exceeded with {self._substrate.url}. No more fallback chains."
                )
                raise MaxRetriesExceeded

    def _reinstantiate_substrate(self, e: Optional[Exception] = None) -> None:
        next_network = next(self.fallback_chains)
        if e.__class__ == MaxRetriesExceeded:
            logging.error(
                f"Max retries exceeded with {self._substrate.url}. Retrying with {next_network}."
            )
        else:
            print(f"Connection error. Trying again with {next_network}")
        self._substrate = self._substrate_class(
            url=next_network,
            ss58_format=self.ss58_format,
            type_registry=self.type_registry,
            use_remote_preset=self.use_remote_preset,
            chain_name=self.chain_name,
            _mock=self._mock,
        )
