from typing import Union
from pymodaq_gui.parameter import Parameter
from pathlib import Path
from pymodaq_gui.parameter import ioxml
from pymodaq_data.h5modules.saving import GROUP
from pymodaq_data.h5modules.saving import H5SaverLowLevel
from pymodaq_data.h5modules.saving import DataType
import numpy as np

from pymodaq_gui.parameter.pymodaq_ptypes import GroupParameter

from pymodaq_data.data import DataDim


# TODO dict list doesn't work
# TODO conversion test (XML file <=> Parameter)
# TODO Should I create a file? If yes, where exactly?
# TODO COMMENT


class ParamH5Converter:

    def __init__(self, h5_file: Path = Path('converter_test.h5')):

        self.saver = H5SaverLowLevel()
        self.saver.init_file(Path(h5_file), raw_group_name='settings')

        self.root_node = self.saver.root()

    @staticmethod
    def _convert_to_parameter(parameter):

        if isinstance(parameter, str) or isinstance(parameter, bytes):
            return ioxml.xml_string_to_parameter(parameter)
        elif isinstance(parameter, Path):
            return ioxml.XML_file_to_parameter(parameter)

        return parameter

    def parameter_to_h5(self, parameter: Union[Parameter, str, Path], where: GROUP = None):

        if where is None:
            current_node = self.root_node
        else:
            current_node = where

        parameter = self._convert_to_parameter(parameter)

        self._parameter_to_h5_rec(parameter, current_node)

    def _parameter_to_h5_rec(self, parameter, current_node):

        param_name = parameter.name()
        param_title = parameter.title()
        param_type = parameter.type()

        opts = {k: v for k,v in parameter.opts.items()
                if k not in ['name', 'title']}

        if parameter.hasChildren() or isinstance(parameter, GroupParameter):
            new_node = self.saver.get_set_group(current_node, param_name, param_title)

            for key, value in opts.items():
                new_node.set_attr(key, value)

            for child in parameter.children():
                self._parameter_to_h5_rec(child, new_node)

        # TODO table
        elif param_type == 'table':
            print("Table node.")

        # TODO color
        elif param_type == 'color':
            print("Color node.")

        else:
            param_value = self._convert_value(parameter)

            # TODO Is this ok?
            param_value = np.array([param_value])

            opts['TITLE'] = param_title
            if 'value' in opts:
                opts.pop('value')

            # TODO data_type here?
            if not self.saver.is_node_in_group(where=current_node, name=param_name):
                self.saver.add_array(where=current_node, name=param_name, data_type=DataType.strings,
                                     array_to_save=param_value, metadata=opts, data_dimension=DataDim.Data0D)

    @staticmethod
    def _convert_value(parameter: Parameter):
        param_value = parameter.value()
        param_type = parameter.type()

        # TODO How to handle None values?
        if param_value is None:
            return ''

        if param_type == 'itemselect':
            return param_value['selected']
        elif param_type == 'date_time':
            return param_value.toPyDateTime().isoformat()
        elif param_type == 'date':
            return param_value.toPyDate().isoformat()
        elif param_type == 'time':
            return param_value.toPyTime().isoformat()

        return param_value

    def close(self):
        self.saver.close_file()
