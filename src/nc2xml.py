#!/usr/bin/env python
"""Hack script to convert a netcdf binary file into various strawman xml formats.

Author: Ben Andre <andre@ucar.edu>

"""

from __future__ import print_function

import sys

if sys.hexversion < 0x02070000:
    print(70 * "*")
    print("ERROR: {0} requires python >= 2.7.x. ".format(sys.argv[0]))
    print("It appears that you are running python {0}".format(
        ".".join(str(x) for x in sys.version_info[0:3])))
    print(70 * "*")
    sys.exit(1)

#
# built-in modules
#
import abc
import argparse
import os
import traceback
import xml.etree.ElementTree as etree
import xml.dom.minidom as minidom

if sys.version_info[0] == 2:
    from ConfigParser import SafeConfigParser as config_parser
else:
    from configparser import ConfigParser as config_parser

#
# installed dependencies
#
import numpy as np
import scipy.io.netcdf as netcdf

#
# other modules in this package
#


# -------------------------------------------------------------------------------
#
# User input
#
# -------------------------------------------------------------------------------
def commandline_options():
    """Process the command line arguments.

    """
    parser = argparse.ArgumentParser(
        description='FIXME: python program template.')

    parser.add_argument('--backtrace', action='store_true',
                        help='show exception backtraces as extra debugging '
                        'output')

    parser.add_argument('--config', nargs=1, default=None,
                        help='path to config file')

    parser.add_argument('--debug', action='store_true',
                        help='extra debugging output')

    parser.add_argument('--netcdf-file', nargs=1, required=True,
                        help='path to netcdf file')

    parser.add_argument('--output-file', nargs=1, default=['junk.xml'],
                        help='path to netcdf file')

    options = parser.parse_args()
    return options


def read_config_file(filename):
    """Read the configuration file and process

    """
    print("Reading configuration file : {0}".format(filename))

    cfg_file = os.path.abspath(filename)
    if not os.path.isfile(cfg_file):
        raise RuntimeError("Could not find config file: {0}".format(cfg_file))

    config = config_parser()
    config.read(cfg_file)

    return config


# -------------------------------------------------------------------------------
#
# work functions
#
# -------------------------------------------------------------------------------
class ParameterXML_base(object):

    def __init__(self):
        self._xml_root = etree.Element('parameters')
        self._xml_root.set('xmlns',
                           'https://github.com/escmi/cime')
        self._xml_root.set('xmlns:xsi',
                           'http://www.w3.org/2001/XMLSchema-instance')
        self._xml_root.set('xsi:schemaLocation',
                           'parameters.xsd')

    @abc.abstractmethod
    def extract_variable_metadata(self, nc_file, xml_root):
        """
        """
        pass

    def write(self, filename):
        """Write the xml to disk.

        Note: the element tree implementation outputs string with no white
        space. We must use the dom parser inorder to 'pretty print' a
        version of the file.
        """
        print("Writing {0}".format(options.output_file[0]))
        with open(options.output_file[0], 'w') as junk:
            try:
                etree_str = etree.tostring(self._xml_root)
                dom = minidom.parseString(etree_str)
                dom.writexml(junk, addindent=4*" ", newl="\n")
            except Exception as e:
                print('error writing to file.')
                print(e)


class ParametersXML_v1(ParameterXML_base):

    def __init__(self):
        super(ParametersXML_v1, self).__init__()
        self._xml_root.set('version', '1.0')

    def extract_variable_metadata(self, nc_file):
        """
        """
        xml_scalar_variables = etree.Element('definitions')
        xml_scalar_variables.set('name', 'scalars')
        xml_litterclass_variables = etree.Element('definitions')
        xml_litterclass_variables.set('name', 'litterclass')
        xml_pft_variables = etree.Element('definitions')
        xml_pft_variables.set('name', 'pft')
        xml_name_variables = etree.Element('definitions')
        xml_name_variables.set('name', 'name')

        for var in nc_file.variables:
            if options.debug:
                print("{var} : {data}".format(var=var, data=nc_file.variables[var]))
            elem = etree.Element('variable')
            elem.set('name', var)
            var_type = 'scalar'
            shape = nc_file.variables[var].shape
            dims = nc_file.variables[var].dimensions
            if len(shape) == 0 and len(dims) == 0:
                var_type = 'scalar'
            elif len(shape) == 1 and dims[0] == 'param':
                var_type = 'scalar'
            elif len(shape) == 1 and dims[0] == 'allpfts':
                var_type = 'scalar'
            elif len(shape) == 1 and dims[0] == 'pft':
                var_type = dims[0]
            elif len(shape) == 1 and dims[0] == 'litterclass':
                var_type = dims[0]
            elif len(shape) == 2 and dims[1] == 'string_length':
                var_type = 'name'
            else:
                var_type = ''
                print('skipping : "{0}"  shape = {1}   dims = {2}'.format(var, len(shape), len(dims)))

            self._add_variable_metadata(elem, nc_file.variables[var]._attributes)
            
            if var_type == 'scalar':
                xml_scalar_variables.append(elem)
            elif var_type == 'pft':
                xml_pft_variables.append(elem)
            elif var_type == 'litterclass':
                xml_litterclass_variables.append(elem)
            elif var_type == 'name':
                xml_name_variables.append(elem)
            if options.debug:
                for var in xml_scalar_variables.iter():
                    print(var)

        self._xml_root.append(xml_scalar_variables)
        self._xml_root.append(xml_pft_variables)
        self._xml_root.append(xml_litterclass_variables)
        self._xml_root.append(xml_name_variables)

    def _add_variable_metadata(self, xml_variable, nc_attributes):
        """
        """
        for key in nc_attributes:
            attrib = etree.Element('metadata')
            attrib.set('name', key)
            attrib.text = "{0}".format(nc_attributes[key])
            xml_variable.append(attrib)

        required_metadata = ['units', 'long_name', ]
        for metadata in required_metadata:
            found_md = xml_variable.find('./metadata[@name="{0}"]'.format(metadata))
            if found_md is None:
                md = etree.Element('metadata')
                md.set('name', metadata)
                md.text = 'unknown'
                xml_variable.append(md)
        
    def _create_value_element(self, var_name, nc_var, data_index):
        """
        """
        data = etree.Element('value')
        data.set('name', var_name)
        if nc_var.data.size == 1:
            tmp_data = str(nc_var.getValue())
        elif len(nc_var.dimensions) == 2:
            # assume we have a slice....?
            tmp_data = nc_var.data[data_index]
            str_list = []
            for d in range(len(tmp_data)):
                tmp = ''.join(tmp_data[d]).strip()
                str_list.append(tmp)
            tmp_data = ' '.join(str_list)
        else:
            tmp_data = nc_var.data[data_index]
            tmp_data = np.array2string(tmp_data)
        data.text = tmp_data
        return data

    def _create_group_tree(self, nc_file, xml_variables, xml_data, data_index):
        """
        """
        for var in xml_variables:
            var_name = var.get('name')
            value = self._create_value_element(var_name, nc_file.variables[var_name], data_index)
            xml_data.append(value)

    def _create_data_tree(self, nc_file, group_name, xml_variables):
        """
        """

        xml_data = etree.Element('data')
        xml_data.set('name', group_name)
        for i in range(nc_file.dimensions[group_name]):
            xml_group = etree.Element('group')
            xml_group.set('name', str(i))
            self._create_group_tree(nc_file, xml_variables, xml_group, i)
            xml_data.append(xml_group)
        return xml_data

    def extract_variable_data(self, nc_file):
        """
        """
        # NOTE(bja, 2016-12) scalars are a combination of allpfts,
        # param and undimensioned variables, so we can't easily group
        # them with create_data_tree...
        group_name = 'scalars'
        xml_variables = self._xml_root.find("./definitions[@name='{0}']".format(group_name))
        xml_data = etree.Element('data')
        xml_data.set('name', group_name)
        self._create_group_tree(nc_file, xml_variables, xml_data, 0)
        self._xml_root.append(xml_data)

        np.set_printoptions(threshold=4000)
        group_name = 'name'
        xml_variables = self._xml_root.find("./definitions[@name='{0}']".format(group_name))
        xml_data = etree.Element('data')
        xml_data.set('name', group_name)
        slice_length = nc_file.dimensions['string_length']
        self._create_group_tree(nc_file, xml_variables, xml_data, slice(slice_length))
        self._xml_root.append(xml_data)

        group_name = 'litterclass'
        xml_variables = self._xml_root.find("./definitions[@name='{0}']".format(group_name))
        xml_data = self._create_data_tree(nc_file, group_name, xml_variables)
        self._xml_root.append(xml_data)

        group_name = 'pft'
        xml_variables = self._xml_root.find("./definitions[@name='{0}']".format(group_name))
        xml_data = self._create_data_tree(nc_file, group_name, xml_variables)
        self._xml_root.append(xml_data)



# -------------------------------------------------------------------------------
#
# main
#
# -------------------------------------------------------------------------------

def main(options):
    if options.config:
        config = read_config_file(options.config[0])

    print("Reading {0}".format(options.netcdf_file[0]))
    nc_file = netcdf.netcdf_file(options.netcdf_file[0], 'r')
    print('dims = {0}'.format(nc_file.dimensions))

    params = ParametersXML_v1()
    params.extract_variable_metadata(nc_file)
    params.extract_variable_data(nc_file)

    params.write(options.output_file[0])
    return 0


if __name__ == "__main__":
    options = commandline_options()
    try:
        status = main(options)
        sys.exit(status)
    except Exception as error:
        print(str(error))
        if options.backtrace:
            traceback.print_exc()
        sys.exit(1)
