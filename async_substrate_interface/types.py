import logging
from abc import ABC
from collections import defaultdict
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Union, Any

from bt_decode import PortableRegistry, encode as encode_by_type_string
from scalecodec import ss58_encode, ss58_decode, is_valid_ss58_address
from scalecodec.base import RuntimeConfigurationObject, ScaleBytes
from scalecodec.type_registry import load_type_registry_preset
from scalecodec.types import GenericCall, ScaleType, MultiAccountId

from .const import SS58_FORMAT
from .utils import json


logger = logging.getLogger("async_substrate_interface")


class RuntimeCache:
    blocks: dict[int, "Runtime"]
    block_hashes: dict[str, "Runtime"]
    versions: dict[int, "Runtime"]

    def __init__(self):
        self.blocks = {}
        self.block_hashes = {}
        self.versions = {}

    def add_item(
        self,
        runtime: "Runtime",
        block: Optional[int] = None,
        block_hash: Optional[str] = None,
        runtime_version: Optional[int] = None,
    ):
        if block is not None:
            self.blocks[block] = runtime
        if block_hash is not None:
            self.block_hashes[block_hash] = runtime
        if runtime_version is not None:
            self.versions[runtime_version] = runtime

    def retrieve(
        self,
        block: Optional[int] = None,
        block_hash: Optional[str] = None,
        runtime_version: Optional[int] = None,
    ) -> Optional["Runtime"]:
        if block is not None:
            return self.blocks.get(block)
        elif block_hash is not None:
            return self.block_hashes.get(block_hash)
        elif runtime_version is not None:
            return self.versions.get(runtime_version)
        else:
            return None


class Runtime:
    runtime_version = None
    transaction_version = None
    cache_region = None
    metadata = None
    metadata_v15 = None
    runtime_config: RuntimeConfigurationObject
    runtime_info = None
    type_registry_preset = None
    registry: Optional[PortableRegistry] = None

    def __init__(
        self,
        chain,
        runtime_config: RuntimeConfigurationObject,
        metadata,
        type_registry,
        metadata_v15=None,
        runtime_info=None,
        registry=None,
    ):
        self.config = {}
        self.chain = chain
        self.type_registry = type_registry
        self.runtime_config = runtime_config
        self.metadata = metadata
        self.metadata_v15 = metadata_v15
        self.runtime_info = runtime_info
        self.registry = registry
        self.runtime_version = runtime_info.get("specVersion")
        self.transaction_version = runtime_info.get("transactionVersion")

    def __str__(self):
        return f"Runtime: {self.chain} | {self.config}"


#    @property
#    def implements_scaleinfo(self) -> bool:
#        """
#        Returns True if current runtime implementation a `PortableRegistry` (`MetadataV14` and higher)
#        """
#        if self.metadata:
#            return self.metadata.portable_registry is not None
#        else:
#            return False
#
#    def reload_type_registry(
#        self, use_remote_preset: bool = True, auto_discover: bool = True
#    ):
#        """
#        Reload type registry and preset used to instantiate the SubstrateInterface object. Useful to periodically apply
#        changes in type definitions when a runtime upgrade occurred
#
#        Args:
#            use_remote_preset: When True preset is downloaded from Github master, otherwise use files from local
#                installed scalecodec package
#            auto_discover: Whether to automatically discover the type registry presets based on the chain name and the
#                type registry
#        """
#        self.runtime_config.clear_type_registry()
#
#        self.runtime_config.implements_scale_info = self.implements_scaleinfo
#
#        # Load metadata types in runtime configuration
#        self.runtime_config.update_type_registry(load_type_registry_preset(name="core"))
#        self.apply_type_registry_presets(
#            use_remote_preset=use_remote_preset, auto_discover=auto_discover
#        )
#
#    def apply_type_registry_presets(
#        self,
#        use_remote_preset: bool = True,
#        auto_discover: bool = True,
#    ):
#        """
#        Applies type registry presets to the runtime
#
#        Args:
#            use_remote_preset: whether to use presets from remote
#            auto_discover: whether to use presets from local installed scalecodec package
#        """
#        if self.type_registry_preset is not None:
#            # Load type registry according to preset
#            type_registry_preset_dict = load_type_registry_preset(
#                name=self.type_registry_preset, use_remote_preset=use_remote_preset
#            )
#
#            if not type_registry_preset_dict:
#                raise ValueError(
#                    f"Type registry preset '{self.type_registry_preset}' not found"
#                )
#
#        elif auto_discover:
#            # Try to auto discover type registry preset by chain name
#            type_registry_name = self.chain.lower().replace(" ", "-")
#            try:
#                type_registry_preset_dict = load_type_registry_preset(
#                    type_registry_name
#                )
#                self.type_registry_preset = type_registry_name
#            except ValueError:
#                type_registry_preset_dict = None
#
#        else:
#            type_registry_preset_dict = None
#
#        if type_registry_preset_dict:
#            # Load type registries in runtime configuration
#            if self.implements_scaleinfo is False:
#                # Only runtime with no embedded types in metadata need the default set of explicit defined types
#                self.runtime_config.update_type_registry(
#                    load_type_registry_preset(
#                        "legacy", use_remote_preset=use_remote_preset
#                    )
#                )
#
#            if self.type_registry_preset != "legacy":
#                self.runtime_config.update_type_registry(type_registry_preset_dict)
#
#        if self.type_registry:
#            # Load type registries in runtime configuration
#            self.runtime_config.update_type_registry(self.type_registry)


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
    type_registry_preset = None
    transaction_version = None
    last_block_hash: Optional[str] = None
    _name: Optional[str] = None
    _properties = None
    _version = None
    _token_decimals = None
    _token_symbol = None
    _chain: str
    runtime_config: RuntimeConfigurationObject
    type_registry: Optional[dict]
    ss58_format: Optional[int]
    ws_max_size = 2**32
    registry_type_map: dict[str, int]
    type_id_to_name: dict[int, str]
    runtime: Runtime = None

    @property
    def chain(self):
        """
        Returns the substrate chain currently associated with object
        """
        return self._chain

    @property
    def metadata(self):
        if not self.runtime or self.runtime.metadata is None:
            raise AttributeError(
                "Metadata not found. This generally indicates that the AsyncSubstrateInterface object "
                "is not properly async initialized."
            )
        else:
            return self.runtime.metadata

    @property
    def implements_scaleinfo(self) -> Optional[bool]:
        """
        Returns True if current runtime implementation a `PortableRegistry` (`MetadataV14` and higher)

        Returns
        -------
        bool
        """
        if self.runtime and self.runtime.metadata:
            return self.runtime.metadata.portable_registry is not None
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

    def _load_registry_type_map(self, registry):
        registry_type_map = {}
        type_id_to_name = {}
        types = json.loads(registry.registry)["types"]
        type_by_id = {entry["id"]: entry for entry in types}

        # Pass 1: Gather simple types
        for type_entry in types:
            type_id = type_entry["id"]
            type_def = type_entry["type"]["def"]
            type_path = type_entry["type"].get("path")
            if type_entry.get("params") or "variant" in type_def:
                continue
            if type_path:
                type_name = type_path[-1]
                registry_type_map[type_name] = type_id
                type_id_to_name[type_id] = type_name
            else:
                # Possibly a primitive
                if "primitive" in type_def:
                    prim_name = type_def["primitive"]
                    registry_type_map[prim_name] = type_id
                    type_id_to_name[type_id] = prim_name

        # Pass 2: Resolve remaining types
        pending_ids = set(type_by_id.keys()) - set(type_id_to_name.keys())

        def resolve_type_definition(type_id_):
            type_entry_ = type_by_id[type_id_]
            type_def_ = type_entry_["type"]["def"]
            type_path_ = type_entry_["type"].get("path", [])
            type_params = type_entry_["type"].get("params", [])

            if type_id_ in type_id_to_name:
                return type_id_to_name[type_id_]

            # Resolve complex types with paths (including generics like Option etc)
            if type_path_:
                type_name_ = type_path_[-1]
                if type_params:
                    inner_names = []
                    for param in type_params:
                        dep_id = param["type"]
                        if dep_id not in type_id_to_name:
                            return None
                        inner_names.append(type_id_to_name[dep_id])
                    return f"{type_name_}<{', '.join(inner_names)}>"
                if "variant" in type_def_:
                    return None
                return type_name_

            elif "sequence" in type_def_:
                sequence_type_id = type_def_["sequence"]["type"]
                inner_type = type_id_to_name.get(sequence_type_id)
                if inner_type:
                    type_name_ = f"Vec<{inner_type}>"
                    return type_name_

            elif "array" in type_def_:
                array_type_id = type_def_["array"]["type"]
                inner_type = type_id_to_name.get(array_type_id)
                maybe_len = type_def_["array"].get("len")
                if inner_type:
                    if maybe_len:
                        type_name_ = f"[{inner_type}; {maybe_len}]"
                    else:
                        type_name_ = f"[{inner_type}]"
                    return type_name_

            elif "compact" in type_def_:
                compact_type_id = type_def_["compact"]["type"]
                inner_type = type_id_to_name.get(compact_type_id)
                if inner_type:
                    type_name_ = f"Compact<{inner_type}>"
                    return type_name_

            elif "tuple" in type_def_:
                tuple_type_ids = type_def_["tuple"]
                type_names = []
                for inner_type_id in tuple_type_ids:
                    if inner_type_id not in type_id_to_name:
                        return None
                    type_names.append(type_id_to_name[inner_type_id])
                type_name_ = ", ".join(type_names)
                type_name_ = f"({type_name_})"
                return type_name_

            elif "variant" in type_def_:
                return None

            return None

        resolved_type = True
        while resolved_type and pending_ids:
            resolved_type = False
            for type_id in list(pending_ids):
                name = resolve_type_definition(type_id)
                if name is not None:
                    type_id_to_name[type_id] = name
                    registry_type_map[name] = type_id
                    pending_ids.remove(type_id)
                    resolved_type = True

        self.registry_type_map = registry_type_map
        self.type_id_to_name = type_id_to_name

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
                logger.debug(
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
            try:
                vec_acct_id = (
                    f"scale_info::{self.registry_type_map['Vec<AccountId32>']}"
                )
            except KeyError:
                vec_acct_id = "scale_info::152"
            try:
                optional_acct_u16 = f"scale_info::{self.registry_type_map['Option<(AccountId32, u16)>']}"
            except KeyError:
                optional_acct_u16 = "scale_info::579"

            if type_string == "scale_info::0":  # Is an AccountId
                # encode string into AccountId
                ## AccountId is a composite type with one, unnamed field
                return self._encode_account_id(value)

            elif type_string == optional_acct_u16:
                if value is None:
                    return b"\x00"  # None

                if not isinstance(value, (list, tuple)) or len(value) != 2:
                    raise ValueError("Expected tuple of (account_id, u16)")
                account_id, u16_value = value

                result = b"\x01"
                result += self._encode_account_id(account_id)
                result += u16_value.to_bytes(2, "little")
                return result

            elif type_string == vec_acct_id:  # Vec<AccountId>
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
                    result += self._encode_account_id(account)
                return result

            if isinstance(value, ScaleType):
                if value.data.data is not None:
                    # Already encoded
                    return bytes(value.data.data)
                else:
                    value = value.value  # Unwrap the value of the type

            result = bytes(
                encode_by_type_string(type_string, self.runtime.registry, value)
            )
        return result

    def _encode_account_id(self, account) -> bytes:
        """Encode an account ID into bytes.

        Args:
            account: Either bytes (already encoded) or SS58 string

        Returns:
            bytes: The encoded account ID
        """
        if isinstance(account, bytes):
            return account  # Already encoded
        return bytes.fromhex(ss58_decode(account, SS58_FORMAT))  # SS58 string

    def generate_multisig_account(
        self, signatories: list, threshold: int
    ) -> MultiAccountId:
        """
        Generate deterministic Multisig account with supplied signatories and threshold

        Args:
            signatories: List of signatories
            threshold: Amount of approvals needed to execute

        Returns:
            MultiAccountId
        """

        multi_sig_account = MultiAccountId.create_from_account_list(
            signatories, threshold
        )

        multi_sig_account.ss58_address = ss58_encode(
            multi_sig_account.value.replace("0x", ""), self.ss58_format
        )

        return multi_sig_account
