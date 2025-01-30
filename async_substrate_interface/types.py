import logging
from abc import ABC
from collections import defaultdict
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Union, Any

from bt_decode import PortableRegistry, encode as encode_by_type_string
from bittensor_wallet.utils import SS58_FORMAT
from scalecodec import ss58_encode, ss58_decode, is_valid_ss58_address
from scalecodec.base import RuntimeConfigurationObject, ScaleBytes
from scalecodec.type_registry import load_type_registry_preset
from scalecodec.types import GenericCall, ScaleType


class RuntimeCache:
    blocks: dict[int, "Runtime"]
    block_hashes: dict[str, "Runtime"]

    def __init__(self):
        self.blocks = {}
        self.block_hashes = {}

    def add_item(
        self, block: Optional[int], block_hash: Optional[str], runtime: "Runtime"
    ):
        if block is not None:
            self.blocks[block] = runtime
        if block_hash is not None:
            self.block_hashes[block_hash] = runtime

    def retrieve(
        self, block: Optional[int] = None, block_hash: Optional[str] = None
    ) -> Optional["Runtime"]:
        if block is not None:
            return self.blocks.get(block)
        elif block_hash is not None:
            return self.block_hashes.get(block_hash)
        else:
            return None


class Runtime:
    block_hash: str
    block_id: int
    runtime_version = None
    transaction_version = None
    cache_region = None
    metadata = None
    runtime_config: RuntimeConfigurationObject
    type_registry_preset = None

    def __init__(
        self, chain, runtime_config: RuntimeConfigurationObject, metadata, type_registry
    ):
        self.config = {}
        self.chain = chain
        self.type_registry = type_registry
        self.runtime_config = runtime_config
        self.metadata = metadata

    def __str__(self):
        return f"Runtime: {self.chain} | {self.config}"

    @property
    def implements_scaleinfo(self) -> bool:
        """
        Returns True if current runtime implementation a `PortableRegistry` (`MetadataV14` and higher)
        """
        if self.metadata:
            return self.metadata.portable_registry is not None
        else:
            return False

    def reload_type_registry(
        self, use_remote_preset: bool = True, auto_discover: bool = True
    ):
        """
        Reload type registry and preset used to instantiate the SubstrateInterface object. Useful to periodically apply
        changes in type definitions when a runtime upgrade occurred

        Args:
            use_remote_preset: When True preset is downloaded from Github master, otherwise use files from local
                installed scalecodec package
            auto_discover: Whether to automatically discover the type registry presets based on the chain name and the
                type registry
        """
        self.runtime_config.clear_type_registry()

        self.runtime_config.implements_scale_info = self.implements_scaleinfo

        # Load metadata types in runtime configuration
        self.runtime_config.update_type_registry(load_type_registry_preset(name="core"))
        self.apply_type_registry_presets(
            use_remote_preset=use_remote_preset, auto_discover=auto_discover
        )

    def apply_type_registry_presets(
        self,
        use_remote_preset: bool = True,
        auto_discover: bool = True,
    ):
        """
        Applies type registry presets to the runtime

        Args:
            use_remote_preset: whether to use presets from remote
            auto_discover: whether to use presets from local installed scalecodec package
        """
        if self.type_registry_preset is not None:
            # Load type registry according to preset
            type_registry_preset_dict = load_type_registry_preset(
                name=self.type_registry_preset, use_remote_preset=use_remote_preset
            )

            if not type_registry_preset_dict:
                raise ValueError(
                    f"Type registry preset '{self.type_registry_preset}' not found"
                )

        elif auto_discover:
            # Try to auto discover type registry preset by chain name
            type_registry_name = self.chain.lower().replace(" ", "-")
            try:
                type_registry_preset_dict = load_type_registry_preset(
                    type_registry_name
                )
                self.type_registry_preset = type_registry_name
            except ValueError:
                type_registry_preset_dict = None

        else:
            type_registry_preset_dict = None

        if type_registry_preset_dict:
            # Load type registries in runtime configuration
            if self.implements_scaleinfo is False:
                # Only runtime with no embedded types in metadata need the default set of explicit defined types
                self.runtime_config.update_type_registry(
                    load_type_registry_preset(
                        "legacy", use_remote_preset=use_remote_preset
                    )
                )

            if self.type_registry_preset != "legacy":
                self.runtime_config.update_type_registry(type_registry_preset_dict)

        if self.type_registry:
            # Load type registries in runtime configuration
            self.runtime_config.update_type_registry(self.type_registry)


class RequestManager:
    RequestResults = dict[Union[str, int], list[Union[ScaleType, dict]]]

    def __init__(self, payloads):
        self.response_map = {}
        self.responses = defaultdict(lambda: {"complete": False, "results": []})
        self.payloads_count = len(payloads)

    def add_request(self, item_id: int, request_id: Any):
        """
        Adds an outgoing request to the responses map for later retrieval
        """
        self.response_map[item_id] = request_id

    def overwrite_request(self, item_id: int, request_id: Any):
        """
        Overwrites an existing request in the responses map with a new request_id. This is used
        for multipart responses that generate a subscription id we need to watch, rather than the initial
        request_id.
        """
        self.response_map[request_id] = self.response_map.pop(item_id)
        return request_id

    def add_response(self, item_id: int, response: dict, complete: bool):
        """
        Maps a response to the request for later retrieval
        """
        request_id = self.response_map[item_id]
        self.responses[request_id]["results"].append(response)
        self.responses[request_id]["complete"] = complete

    @property
    def is_complete(self) -> bool:
        """
        Returns whether all requests in the manager have completed
        """
        return (
            all(info["complete"] for info in self.responses.values())
            and len(self.responses) == self.payloads_count
        )

    def get_results(self) -> RequestResults:
        """
        Generates a dictionary mapping the requests initiated to the responses received.
        """
        return {
            request_id: info["results"] for request_id, info in self.responses.items()
        }


@dataclass
class Preprocessed:
    queryable: str
    method: str
    params: list
    value_scale_type: str
    storage_item: ScaleType


class ScaleObj:
    """Bittensor representation of Scale Object."""

    def __init__(self, value):
        self.value = list(value) if isinstance(value, tuple) else value

    def __new__(cls, value):
        return super().__new__(cls)

    def __str__(self):
        return f"BittensorScaleType(value={self.value})>"

    def __bool__(self):
        if self.value:
            return True
        else:
            return False

    def __repr__(self):
        return repr(f"BittensorScaleType(value={self.value})>")

    def __eq__(self, other):
        return self.value == (other.value if isinstance(other, ScaleObj) else other)

    def __lt__(self, other):
        return self.value < (other.value if isinstance(other, ScaleObj) else other)

    def __gt__(self, other):
        return self.value > (other.value if isinstance(other, ScaleObj) else other)

    def __le__(self, other):
        return self.value <= (other.value if isinstance(other, ScaleObj) else other)

    def __ge__(self, other):
        return self.value >= (other.value if isinstance(other, ScaleObj) else other)

    def __add__(self, other):
        if isinstance(other, ScaleObj):
            return ScaleObj(self.value + other.value)
        return ScaleObj(self.value + other)

    def __radd__(self, other):
        return ScaleObj(other + self.value)

    def __sub__(self, other):
        if isinstance(other, ScaleObj):
            return ScaleObj(self.value - other.value)
        return ScaleObj(self.value - other)

    def __rsub__(self, other):
        return ScaleObj(other - self.value)

    def __mul__(self, other):
        if isinstance(other, ScaleObj):
            return ScaleObj(self.value * other.value)
        return ScaleObj(self.value * other)

    def __rmul__(self, other):
        return ScaleObj(other * self.value)

    def __truediv__(self, other):
        if isinstance(other, ScaleObj):
            return ScaleObj(self.value / other.value)
        return ScaleObj(self.value / other)

    def __rtruediv__(self, other):
        return ScaleObj(other / self.value)

    def __floordiv__(self, other):
        if isinstance(other, ScaleObj):
            return ScaleObj(self.value // other.value)
        return ScaleObj(self.value // other)

    def __rfloordiv__(self, other):
        return ScaleObj(other // self.value)

    def __mod__(self, other):
        if isinstance(other, ScaleObj):
            return ScaleObj(self.value % other.value)
        return ScaleObj(self.value % other)

    def __rmod__(self, other):
        return ScaleObj(other % self.value)

    def __pow__(self, other):
        if isinstance(other, ScaleObj):
            return ScaleObj(self.value**other.value)
        return ScaleObj(self.value**other)

    def __rpow__(self, other):
        return ScaleObj(other**self.value)

    def __getitem__(self, key):
        if isinstance(self.value, (list, tuple, dict, str)):
            return self.value[key]
        raise TypeError(
            f"Object of type '{type(self.value).__name__}' does not support indexing"
        )

    def __iter__(self):
        if isinstance(self.value, Iterable):
            return iter(self.value)
        raise TypeError(f"Object of type '{type(self.value).__name__}' is not iterable")

    def __len__(self):
        return len(self.value)

    def process(self):
        pass

    def serialize(self):
        return self.value

    def decode(self):
        return self.value


class SubstrateMixin(ABC):
    registry: Optional[PortableRegistry] = None
    runtime_version = None
    type_registry_preset = None
    transaction_version = None
    block_id: Optional[int] = None
    last_block_hash: Optional[str] = None
    _name: Optional[str] = None
    _properties = None
    _version = None
    _token_decimals = None
    _token_symbol = None
    _metadata = None
    _chain: str
    runtime_config: RuntimeConfigurationObject
    type_registry: Optional[dict]
    ss58_format: Optional[int]

    @property
    def chain(self):
        """
        Returns the substrate chain currently associated with object
        """
        return self._chain

    @property
    def metadata(self):
        if self._metadata is None:
            raise AttributeError(
                "Metadata not found. This generally indicates that the AsyncSubstrateInterface object "
                "is not properly async initialized."
            )
        else:
            return self._metadata

    @property
    def runtime(self):
        return Runtime(
            self.chain,
            self.runtime_config,
            self._metadata,
            self.type_registry,
        )

    @property
    def implements_scaleinfo(self) -> Optional[bool]:
        """
        Returns True if current runtime implementation a `PortableRegistry` (`MetadataV14` and higher)

        Returns
        -------
        bool
        """
        if self._metadata:
            return self._metadata.portable_registry is not None
        else:
            return None

    def ss58_encode(
        self, public_key: Union[str, bytes], ss58_format: int = None
    ) -> str:
        """
        Helper function to encode a public key to SS58 address.

        If no target `ss58_format` is provided, it will default to the ss58 format of the network it's connected to.

        Args:
            public_key: 32 bytes or hex-string. e.g. 0x6e39f36c370dd51d9a7594846914035de7ea8de466778ea4be6c036df8151f29
            ss58_format: target networkID to format the address for, defaults to the network it's connected to

        Returns:
            str containing the SS58 address
        """

        if ss58_format is None:
            ss58_format = self.ss58_format

        return ss58_encode(public_key, ss58_format=ss58_format)

    def ss58_decode(self, ss58_address: str) -> str:
        """
        Helper function to decode a SS58 address to a public key

        Args:
            ss58_address: the encoded SS58 address to decode (e.g. EaG2CRhJWPb7qmdcJvy3LiWdh26Jreu9Dx6R1rXxPmYXoDk)

        Returns:
            str containing the hex representation of the public key
        """
        return ss58_decode(ss58_address, valid_ss58_format=self.ss58_format)

    def is_valid_ss58_address(self, value: str) -> bool:
        """
        Helper function to validate given value as ss58_address for current network/ss58_format

        Args:
            value: value to validate

        Returns:
            bool
        """
        return is_valid_ss58_address(value, valid_ss58_format=self.ss58_format)

    def serialize_storage_item(
        self, storage_item: ScaleType, module, spec_version_id
    ) -> dict:
        """
        Helper function to serialize a storage item

        Args:
            storage_item: the storage item to serialize
            module: the module to use to serialize the storage item
            spec_version_id: the version id

        Returns:
            dict
        """
        storage_dict = {
            "storage_name": storage_item.name,
            "storage_modifier": storage_item.modifier,
            "storage_default_scale": storage_item["default"].get_used_bytes(),
            "storage_default": None,
            "documentation": "\n".join(storage_item.docs),
            "module_id": module.get_identifier(),
            "module_prefix": module.value["storage"]["prefix"],
            "module_name": module.name,
            "spec_version": spec_version_id,
            "type_keys": storage_item.get_params_type_string(),
            "type_hashers": storage_item.get_param_hashers(),
            "type_value": storage_item.get_value_type_string(),
        }

        type_class, type_info = next(iter(storage_item.type.items()))

        storage_dict["type_class"] = type_class

        value_scale_type = storage_item.get_value_type_string()

        if storage_item.value["modifier"] == "Default":
            # Fallback to default value of storage function if no result
            query_value = storage_item.value_object["default"].value_object
        else:
            # No result is interpreted as an Option<...> result
            value_scale_type = f"Option<{value_scale_type}>"
            query_value = storage_item.value_object["default"].value_object

        try:
            obj = self.runtime_config.create_scale_object(
                type_string=value_scale_type,
                data=ScaleBytes(query_value),
                metadata=self.metadata,
            )
            obj.decode()
            storage_dict["storage_default"] = obj.decode()
        except Exception:
            storage_dict["storage_default"] = "[decoding error]"

        return storage_dict

    def serialize_constant(self, constant, module, spec_version_id) -> dict:
        """
        Helper function to serialize a constant

        Parameters
        ----------
        constant
        module
        spec_version_id

        Returns
        -------
        dict
        """
        try:
            value_obj = self.runtime_config.create_scale_object(
                type_string=constant.type, data=ScaleBytes(constant.constant_value)
            )
            constant_decoded_value = value_obj.decode()
        except Exception:
            constant_decoded_value = "[decoding error]"

        return {
            "constant_name": constant.name,
            "constant_type": constant.type,
            "constant_value": constant_decoded_value,
            "constant_value_scale": f"0x{constant.constant_value.hex()}",
            "documentation": "\n".join(constant.docs),
            "module_id": module.get_identifier(),
            "module_prefix": module.value["storage"]["prefix"]
            if module.value["storage"]
            else None,
            "module_name": module.name,
            "spec_version": spec_version_id,
        }

    @staticmethod
    def serialize_module_call(module, call: GenericCall, spec_version) -> dict:
        """
        Helper function to serialize a call function

        Args:
            module: the module to use
            call: the call function to serialize
            spec_version: the spec version of the call function

        Returns:
            dict serialized version of the call function
        """
        return {
            "call_name": call.name,
            "call_args": [call_arg.value for call_arg in call.args],
            "documentation": "\n".join(call.docs),
            "module_prefix": module.value["storage"]["prefix"]
            if module.value["storage"]
            else None,
            "module_name": module.name,
            "spec_version": spec_version,
        }

    @staticmethod
    def serialize_module_event(module, event, spec_version, event_index: str) -> dict:
        """
        Helper function to serialize an event

        Args:
            module: the metadata module
            event: the event to serialize
            spec_version: the spec version of the error
            event_index: the hex index of this event in the block

        Returns:
            dict serialized version of the event
        """
        return {
            "event_id": event.name,
            "event_name": event.name,
            "event_args": [
                {"event_arg_index": idx, "type": arg}
                for idx, arg in enumerate(event.args)
            ],
            "lookup": f"0x{event_index}",
            "documentation": "\n".join(event.docs),
            "module_id": module.get_identifier(),
            "module_prefix": module.prefix,
            "module_name": module.name,
            "spec_version": spec_version,
        }

    @staticmethod
    def serialize_module_error(module, error, spec_version) -> dict:
        """
        Helper function to serialize an error

        Args:
            module: the metadata module
            error: the error to serialize
            spec_version: the spec version of the error

        Returns:
            dict serialized version of the module error
        """
        return {
            "error_name": error.name,
            "documentation": "\n".join(error.docs),
            "module_id": module.get_identifier(),
            "module_prefix": module.value["storage"]["prefix"]
            if module.value["storage"]
            else None,
            "module_name": module.name,
            "spec_version": spec_version,
        }

    def reload_type_registry(
        self, use_remote_preset: bool = True, auto_discover: bool = True
    ):
        """
        Reload type registry and preset used to instantiate the `AsyncSubstrateInterface` object. Useful to
        periodically apply changes in type definitions when a runtime upgrade occurred

        Args:
            use_remote_preset: When True preset is downloaded from Github master,
                otherwise use files from local installed scalecodec package
            auto_discover: Whether to automatically discover the type_registry
                presets based on the chain name and typer registry
        """
        self.runtime_config.clear_type_registry()

        self.runtime_config.implements_scale_info = self.implements_scaleinfo

        # Load metadata types in runtime configuration
        self.runtime_config.update_type_registry(load_type_registry_preset(name="core"))
        self.apply_type_registry_presets(
            use_remote_preset=use_remote_preset, auto_discover=auto_discover
        )

    def apply_type_registry_presets(
        self, use_remote_preset: bool = True, auto_discover: bool = True
    ):
        if self.type_registry_preset is not None:
            # Load type registry according to preset
            type_registry_preset_dict = load_type_registry_preset(
                name=self.type_registry_preset, use_remote_preset=use_remote_preset
            )

            if not type_registry_preset_dict:
                raise ValueError(
                    f"Type registry preset '{self.type_registry_preset}' not found"
                )

        elif auto_discover:
            # Try to auto discover type registry preset by chain name
            type_registry_name = self.chain.lower().replace(" ", "-")
            try:
                type_registry_preset_dict = load_type_registry_preset(
                    type_registry_name
                )
                logging.debug(
                    f"Auto set type_registry_preset to {type_registry_name} ..."
                )
                self.type_registry_preset = type_registry_name
            except ValueError:
                type_registry_preset_dict = None

        else:
            type_registry_preset_dict = None

        if type_registry_preset_dict:
            # Load type registries in runtime configuration
            if self.implements_scaleinfo is False:
                # Only runtime with no embedded types in metadata need the default set of explicit defined types
                self.runtime_config.update_type_registry(
                    load_type_registry_preset(
                        "legacy", use_remote_preset=use_remote_preset
                    )
                )

            if self.type_registry_preset != "legacy":
                self.runtime_config.update_type_registry(type_registry_preset_dict)

        if self.type_registry:
            # Load type registries in runtime configuration
            self.runtime_config.update_type_registry(self.type_registry)

    def extension_call(self, name, **kwargs):
        raise NotImplementedError(
            "Extensions not implemented in AsyncSubstrateInterface"
        )

    def filter_extrinsics(self, **kwargs) -> list:
        return self.extension_call("filter_extrinsics", **kwargs)

    def filter_events(self, **kwargs) -> list:
        return self.extension_call("filter_events", **kwargs)

    def search_block_number(self, block_datetime: datetime, block_time: int = 6) -> int:
        return self.extension_call(
            "search_block_number", block_datetime=block_datetime, block_time=block_time
        )

    def get_block_timestamp(self, block_number: int) -> int:
        return self.extension_call("get_block_timestamp", block_number=block_number)

    @staticmethod
    def make_payload(id_: str, method: str, params: list) -> dict:
        """
        Creates a payload for making an rpc_request with _make_rpc_request

        Args:
            id_: a unique name you would like to give to this request
            method: the method in the RPC request
            params: the params in the RPC request

        Returns:
            the payload dict
        """
        return {
            "id": id_,
            "payload": {"jsonrpc": "2.0", "method": method, "params": params},
        }

    def _encode_scale(self, type_string, value: Any) -> bytes:
        """
        Helper function to encode arbitrary data into SCALE-bytes for given RUST type_string

        Args:
            type_string: the type string of the SCALE object for decoding
            value: value to encode

        Returns:
            encoded bytes
        """
        if value is None:
            result = b"\x00"
        else:
            if type_string == "scale_info::0":  # Is an AccountId
                # encode string into AccountId
                ## AccountId is a composite type with one, unnamed field
                return bytes.fromhex(ss58_decode(value, SS58_FORMAT))

            elif type_string == "scale_info::151":  # Vec<AccountId>
                if not isinstance(value, (list, tuple)):
                    value = [value]

                # Encode length
                length = len(value)
                if length < 64:
                    result = bytes([length << 2])  # Single byte mode
                else:
                    raise ValueError("Vector length too large")

                # Encode each AccountId
                for account in value:
                    if isinstance(account, bytes):
                        result += account  # Already encoded
                    else:
                        result += bytes.fromhex(
                            ss58_decode(account, SS58_FORMAT)
                        )  # SS58 string
                return result

            if isinstance(value, ScaleType):
                if value.data.data is not None:
                    # Already encoded
                    return bytes(value.data.data)
                else:
                    value = value.value  # Unwrap the value of the type

            result = bytes(encode_by_type_string(type_string, self.registry, value))
        return result
