from typing import Union

from PyQt6.QtCore import QDateTime
from pymodaq_gui.parameter import Parameter
from pathlib import Path
from pymodaq_gui.parameter import ioxml
from pymodaq_data.h5modules.saving import GROUP
from pymodaq_data.h5modules.saving import H5SaverLowLevel
from pymodaq_data.h5modules.saving import DataType
import numpy as np

from qtpy.QtCore import Qt

from pymodaq_gui.parameter.pymodaq_ptypes import GroupParameter

from pymodaq_data.data import DataDim

# TODO dict list doesn't work?
# TODO COMMENT

# TODO Add a 'settings' group as I do or not?

class ParamH5Converter:

    def __init__(self, parameter: Union[Parameter, str, Path]):

        self.saver = None
        self.parameter = self._convert_to_parameter(parameter)

    @staticmethod
    def _convert_to_parameter(parameter):

        if isinstance(parameter, str) or isinstance(parameter, bytes):
            return ioxml.xml_string_to_parameter(parameter)
        elif isinstance(parameter, Path):
            return ioxml.xml_file_to_parameter(parameter)

        return parameter

    # TODO Return to 2 params where and h5_file or keep this?
    def parameter_to_h5(self, target: Union[GROUP, Path]):

        if isinstance(target, GROUP):
            saver_init = False

            # TODO how to handle GROUP?
            current_node = target.node
            self.saver = target.to_h5_backend()
            current_node = self.saver.get_set_group(current_node, 'settings')
        else:
            self.saver = H5SaverLowLevel()
            self.saver.init_file(target, raw_group_name='settings')
            saver_init = True
            current_node = self.saver.root()

        self._parameter_to_h5_rec(self.parameter, current_node)

        if saver_init:
            self.saver.close_file()

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

        else:
            param_value = self._convert_value(parameter)

            # TODO Is this ok?
            if param_type != 'table' and param_type != 'table_view':
                param_value = np.array([param_value])

            opts['TITLE'] = param_title
            if 'value' in opts:
                opts.pop('value')

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
            return param_value.toString(Qt.DateFormat.ISODate)

        elif param_type == 'date':
            return param_value.toString(Qt.DateFormat.ISODate)

        elif param_type == 'time':
            return param_value.toString(Qt.DateFormat.ISODate)
        # TODO Is this ok? Same thing in ioxml

        elif param_type == 'color':
            return str([param_value.red(), param_value.green(), param_value.blue(), param_value.alpha()])

        elif param_type == 'table':
            return np.array(list(param_value.items()), parameter.opts.get('header'))

        """elif param_type == 'table_view':
            row_count = param_value.rowCount()
            col_count = param_value.columnCount()
            data_array = {param_value.index(i,j).data(Qt.ItemDataRole.DisplayRole) for i in range(row_count) for j in range(col_count)}
            return np.array(list(data_array))"""

        return param_value
