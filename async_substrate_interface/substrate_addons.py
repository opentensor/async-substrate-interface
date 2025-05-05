import asyncio
import logging
from functools import partial
from itertools import cycle
from typing import Optional

from async_substrate_interface.async_substrate import AsyncSubstrateInterface
from async_substrate_interface.errors import MaxRetriesExceeded
from async_substrate_interface.sync_substrate import SubstrateInterface


RETRY_METHODS = [
    "_get_block_handler",
    "apply_type_registry_presets",
    "close",
    "compose_call",
    "connect",
    "create_scale_object",
    "create_signed_extrinsic",
    "create_storage_key",
    "decode_scale",
    "encode_scale",
    "extension_call",
    "filter_events",
    "filter_extrinsics",
    "generate_signature_payload",
    "get_account_next_index",
    "get_account_nonce",
    "get_block",
    "get_block_hash",
    "get_block_header",
    "get_block_metadata",
    "get_block_number",
    "get_block_runtime_info",
    "get_block_runtime_version_for",
    "get_block_timestamp",
    "get_chain_finalised_head",
    "get_chain_head",
    "get_constant",
    "get_events",
    "get_extrinsics",
    "get_metadata_call_function",
    "get_metadata_constant",
    "get_metadata_error",
    "get_metadata_errors",
    "get_metadata_module",
    "get_metadata_modules",
    "get_metadata_runtime_call_function",
    "get_metadata_runtime_call_functions",
    "get_metadata_storage_function",
    "get_metadata_storage_functions",
    "get_parent_block_hash",
    "get_payment_info",
    "get_storage_item",
    "get_type_definition",
    "get_type_registry",
    "init_runtime",
    "initialize",
    "is_valid_ss58_address",
    "load_runtime",
    "make_payload",
    "query",
    "query_map",
    "query_multi",
    "query_multiple",
    "reload_type_registry",
    "retrieve_extrinsic_by_hash",
    "retrieve_extrinsic_by_identifier",
    "rpc_request",
    "runtime_call",
    "search_block_number",
    "serialize_constant",
    "serialize_module_call",
    "serialize_module_error",
    "serialize_module_event",
    "serialize_storage_item",
    "ss58_decode",
    "ss58_encode",
    "submit_extrinsic",
    "subscribe_block_headers",
    "supports_rpc_method",
]

RETRY_PROPS = ["properties", "version", "token_decimals", "token_symbol", "name"]


class RetrySyncSubstrate(SubstrateInterface):
    def __init__(
        self,
        url: str,
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
        self.fallback_chains = (
            iter(fallback_chains)
            if not retry_forever
            else cycle(fallback_chains + [url])
        )
        self.use_remote_preset = use_remote_preset
        self.chain_name = chain_name
        self._mock = _mock
        self.retry_timeout = retry_timeout
        self.max_retries = max_retries
        initialized = False
        for chain_url in [url] + fallback_chains:
            try:
                super().__init__(
                    url=chain_url,
                    ss58_format=ss58_format,
                    type_registry=type_registry,
                    use_remote_preset=use_remote_preset,
                    type_registry_preset=type_registry_preset,
                    chain_name=chain_name,
                    _mock=_mock,
                    retry_timeout=retry_timeout,
                    max_retries=max_retries,
                )
                initialized = True
                break
            except ConnectionError:
                logging.warning(f"Unable to connect to {chain_url}")
        if not initialized:
            raise ConnectionError(
                f"Unable to connect at any chains specified: {[url] + fallback_chains}"
            )
        for method in RETRY_METHODS:
            setattr(self, method, partial(self._retry, method))
        for property_ in RETRY_PROPS:
            setattr(self, property_, partial(self._retry_property, property_))

    def _retry(self, method, *args, **kwargs):
        try:
            method_ = getattr(self, method)
            return method_(*args, **kwargs)
        except (MaxRetriesExceeded, ConnectionError, ConnectionRefusedError) as e:
            try:
                self._reinstantiate_substrate(e)
                method_ = getattr(self, method)
                return self._retry(method_(*args, **kwargs))
            except StopIteration:
                logging.error(
                    f"Max retries exceeded with {self.url}. No more fallback chains."
                )
                raise MaxRetriesExceeded

    def _retry_property(self, property_):
        try:
            return getattr(self, property_)
        except (MaxRetriesExceeded, ConnectionError, ConnectionRefusedError) as e:
            try:
                self._reinstantiate_substrate(e)
                return self._retry_property(property_)
            except StopIteration:
                logging.error(
                    f"Max retries exceeded with {self.url}. No more fallback chains."
                )
                raise MaxRetriesExceeded

    def _reinstantiate_substrate(self, e: Optional[Exception] = None) -> None:
        next_network = next(self.fallback_chains)
        if e.__class__ == MaxRetriesExceeded:
            logging.error(
                f"Max retries exceeded with {self.url}. Retrying with {next_network}."
            )
        else:
            print(f"Connection error. Trying again with {next_network}")
        super().__init__(
            url=next_network,
            ss58_format=self.ss58_format,
            type_registry=self.type_registry,
            use_remote_preset=self.use_remote_preset,
            chain_name=self.chain_name,
            _mock=self._mock,
            retry_timeout=self.retry_timeout,
            max_retries=self.max_retries,
        )


class RetryAsyncSubstrate(AsyncSubstrateInterface):
    def __init__(
        self,
        url: str,
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
        self.fallback_chains = (
            iter(fallback_chains)
            if not retry_forever
            else cycle(fallback_chains + [url])
        )
        self.use_remote_preset = use_remote_preset
        self.chain_name = chain_name
        self._mock = _mock
        self.retry_timeout = retry_timeout
        self.max_retries = max_retries
        super().__init__(
            url=url,
            ss58_format=ss58_format,
            type_registry=type_registry,
            use_remote_preset=use_remote_preset,
            type_registry_preset=type_registry_preset,
            chain_name=chain_name,
            _mock=_mock,
            retry_timeout=retry_timeout,
            max_retries=max_retries,
        )
        for method in RETRY_METHODS:
            setattr(self, method, partial(self._retry, method))
        for property_ in RETRY_PROPS:
            setattr(self, property_, partial(self._retry_property, property_))

    def _reinstantiate_substrate(self, e: Optional[Exception] = None) -> None:
        next_network = next(self.fallback_chains)
        if e.__class__ == MaxRetriesExceeded:
            logging.error(
                f"Max retries exceeded with {self.url}. Retrying with {next_network}."
            )
        else:
            print(f"Connection error. Trying again with {next_network}")
        super().__init__(
            url=next_network,
            ss58_format=self.ss58_format,
            type_registry=self.type_registry,
            use_remote_preset=self.use_remote_preset,
            chain_name=self.chain_name,
            _mock=self._mock,
            retry_timeout=self.retry_timeout,
            max_retries=self.max_retries,
        )

    async def _retry(self, method, *args, **kwargs):
        try:
            method_ = getattr(self, method)
            if asyncio.iscoroutinefunction(method_):
                return await method_(*args, **kwargs)
            else:
                return method_(*args, **kwargs)
        except (MaxRetriesExceeded, ConnectionError, ConnectionRefusedError) as e:
            try:
                self._reinstantiate_substrate(e)
                await self.initialize()
                method_ = getattr(self, method)
                if asyncio.iscoroutinefunction(method_):
                    return await method_(*args, **kwargs)
                else:
                    return method_(*args, **kwargs)
            except StopIteration:
                logging.error(
                    f"Max retries exceeded with {self.url}. No more fallback chains."
                )
                raise MaxRetriesExceeded

    async def _retry_property(self, property_):
        try:
            return await getattr(self, property_)
        except (MaxRetriesExceeded, ConnectionError, ConnectionRefusedError) as e:
            try:
                self._reinstantiate_substrate(e)
                return await self._retry_property(property_)
            except StopIteration:
                logging.error(
                    f"Max retries exceeded with {self.url}. No more fallback chains."
                )
                raise MaxRetriesExceeded
