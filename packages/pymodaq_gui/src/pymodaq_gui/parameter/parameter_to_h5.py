from typing import Union

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

# TODO COMMENT

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

    def parameter_to_h5(self, target: Union[GROUP, Path], saver = None):

        if isinstance(target, GROUP):

            if saver is None:
                raise Exception("Missing parameter: saver.")

            saver_init = False
            self.saver = saver
            current_node = self.saver.get_node(target)
            current_node = self.saver.get_set_group(current_node, 'settings')

        else:
            saver_init = True
            self.saver = H5SaverLowLevel()
            self.saver.init_file(target, raw_group_name='settings')
            current_node = self.saver.root()

        self._parameter_to_h5_rec(self.parameter, current_node)

        if saver_init:
            self.saver.close_file()

    def _parameter_to_h5_rec(self, parameter, current_node):

        param_name = parameter.name()
        param_title = parameter.title()

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
            return np.array([''])

        if param_type == 'itemselect':
            return np.array([param_value['selected']])

        elif param_type == 'date_time' or param_type == 'date' or param_type == 'time':
            return np.array([param_value.toString(Qt.DateFormat.ISODate)])

        elif param_type == 'color':
            return np.array([str([param_value.red(), param_value.green(), param_value.blue(), param_value.alpha()])])

        elif param_type == 'table':
            items = list(param_value.items())
            items = [e[1] for e in items]

            return np.array(items)

        elif param_type == 'table_view':
            row_count = param_value.rowCount()
            col_count = param_value.columnCount()
            data_array = [param_value.index(i,j).data(Qt.ItemDataRole.DisplayRole) for i in range(row_count) for j in range(col_count)]
            return np.array(data_array)

        return np.array([param_value])
