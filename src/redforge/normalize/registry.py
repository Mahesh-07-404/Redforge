from typing import Dict
from .mapper import (
    BaseMapper, SubfinderMapper, AssetfinderMapper, AmassMapper,
    HttpxMapper, KatanaMapper, GAUMapper, WaybackurlsMapper,
    NmapMapper, NaabuMapper, NucleiMapper, DNSXMapper,
    FFUFMapper, FeroxbusterMapper, GobusterMapper
)

class MapperRegistry:
    def __init__(self):
        self._mappers: Dict[str, BaseMapper] = {}
        self._initialize_mappers()

    def _initialize_mappers(self):
        mappers_list = [
            SubfinderMapper(), AssetfinderMapper(), AmassMapper(),
            HttpxMapper(), KatanaMapper(), GAUMapper(), WaybackurlsMapper(),
            NmapMapper(), NaabuMapper(), NucleiMapper(), DNSXMapper(),
            FFUFMapper(), FeroxbusterMapper(), GobusterMapper()
        ]
        for m in mappers_list:
            self.register_mapper(m)

    def register_mapper(self, mapper: BaseMapper):
        self._mappers[mapper.tool_name.lower()] = mapper

    def get_mapper(self, tool_name: str) -> BaseMapper:
        return self._mappers.get(tool_name.lower())
