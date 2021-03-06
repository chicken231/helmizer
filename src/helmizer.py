#!/usr/bin/env python3

"""
Helmizer - Generates `kustomization.yaml` for your locally-rendered YAML manifests,
such as from Helm templates or plain YAML manifests
"""

import argparse
import logging
from os import path, walk
from sys import stdout
import confuse
from confuse.exceptions import NotFoundError
import subprocess

import yaml
from validators import url as validate_url


class Kustomization():
    def __init__(self, helmizer_config, arguments):
        self.helmizer_config = helmizer_config
        self.arguments = arguments
        self.yaml = dict()

        # apiVersion
        self.yaml['apiVersion'] = self.get_api_version()

        # kind
        self.yaml['kind'] = 'Kustomization'

        # namespace
        str_namespace = self.get_namespace()
        if str_namespace:
            self.yaml['namespace'] = str_namespace

        # commonAnnotations
        dict_common_annotations = self.get_common_annotations()
        if dict_common_annotations:
            self.yaml['commonAnnotations'] = dict_common_annotations

        # commonLabels
        dict_get_common_labels = self.get_common_labels()
        if dict_get_common_labels:
            self.yaml['commonLabels'] = dict_get_common_labels

        # crds
        list_crds = self.get_files(arguments, 'crds')
        if list_crds:
            self.yaml['crds'] = list_crds

        # components
        list_components = self.get_files(arguments, 'components')
        if list_components:
            self.yaml['components'] = list_components

        # namePrefix
        str_name_prefix = self.get_name_prefix()
        if str_name_prefix:
            self.yaml['namePrefix'] = str_name_prefix

        # nameSuffix
        str_name_suffix = self.get_name_suffix()
        if str_name_suffix:
            self.yaml['nameSuffix'] = str_name_suffix

        # patchesStrategicMerge
        list_patches_strategic_merge = self.get_files(arguments, 'patchesStrategicMerge')
        if list_patches_strategic_merge:
            self.yaml['patchesStrategicMerge'] = list_patches_strategic_merge

        # resources
        list_resources = self.get_files(arguments, 'resources')
        if list_resources:
            self.yaml['resources'] = list_resources


    def sort_keys(self):
        try:
            self.helmizer_config['helmizer']['sort-keys'].get(bool)
            for array in 'resources', 'patchesStrategicMerge':
                self.yaml[array].sort()
        except KeyError:
            pass


    def print_kustomization(self):
        try:
            print(yaml.dump(self.yaml, sort_keys=False))
        except KeyError:
            print(yaml.dump(self.yaml, sort_keys=False))


    def write_kustomization(self, arguments):
        if self.helmizer_config['helmizer']['dry-run'].get(bool) or arguments.dry_run:
            logging.debug('Performing dry-run, not writing to a file system')
        else:
            # identify kustomization file's parent directory
            str_kustomization_directory = path.dirname(path.abspath(path.normpath(arguments.helmizer_config)))

            # identify kustomization file name
            str_kustomization_file_name = str()
            try:
                str_kustomization_file_name = self.helmizer_config['helmizer']['kustomization-file-name'].get(str)
            except KeyError:
                str_kustomization_file_name = 'kustomization.yaml'

            # write to file
            try:
                kustomization_file_path = path.normpath(f'{str_kustomization_directory}/{str_kustomization_file_name}')
                with open(kustomization_file_path, 'w') as file:
                    file.write(yaml.dump(self.yaml))
                    logging.debug(f'Successfully wrote to file: {path.abspath(kustomization_file_path)}')
            except IsADirectoryError as e:
                raise e
            except TypeError:
                pass


    def render_template(self, arguments):
        logging.debug('Rendering template')
        self.sort_keys()
        self.print_kustomization()
        self.write_kustomization(arguments)


    def get_api_version(self):
        str_api_version = str()
        try:
            str_api_version = self.helmizer_config['kustomize']['apiVersion'].get(str)
        except NotFoundError:
            str_api_version = 'kustomize.config.k8s.io/v1beta1'
        finally:
            logging.debug(f'apiVersion: {str_api_version}')
            return str_api_version


    def get_namespace(self):
        str_namespace = str()
        try:
            if len(self.helmizer_config['kustomize']['namespace'].get(str)) > 0:
                str_namespace = self.helmizer_config['kustomize']['namespace'].get(str)
                logging.debug(f'namespace: {str_namespace}')
        except TypeError:
            pass
        finally:
            return str_namespace


    def get_common_annotations(self):
        dict_common_annotations = dict()
        try:
            if len(self.helmizer_config['kustomize']['commonAnnotations'].get(dict)) > 0:
                dict_common_annotations = dict(self.helmizer_config['kustomize']['commonAnnotations'].get(dict))
                logging.debug(f'commonAnnotations: {dict_common_annotations}')
        except TypeError:
            pass
        finally:
            return dict_common_annotations


    def get_common_labels(self):
        dict_common_labels = dict()
        try:
            if len(self.helmizer_config['kustomize']['commonLabels'].get(dict)) > 0:
                dict_common_labels = dict(self.helmizer_config['kustomize']['commonLabels'].get(dict))
                logging.debug(f'commonLabels: {dict_common_labels}')
        except TypeError:
            pass
        finally:
            return dict_common_labels


    def get_name_prefix(self):
        str_name_prefix = str()
        try:
            if len(self.helmizer_config['kustomize']['namePrefix'].get(str)) > 0:
                str_name_prefix = self.helmizer_config['kustomize']['namePrefix'].get(str)
                logging.debug(f'namespace: {str_name_prefix}')
        except TypeError:
            pass
        finally:
            return str_name_prefix


    def get_name_suffix(self):
        str_name_suffix = str()
        try:
            if len(self.helmizer_config['kustomize']['nameSuffix'].get(str)) > 0:
                str_name_suffix = self.helmizer_config['kustomize']['nameSuffix'].get(str)
                logging.debug(f'namespace: {str_name_suffix}')
        except TypeError:
            pass
        finally:
            return str_name_suffix


    def get_files(self, arguments, key):
        list_target_paths = list()
        list_final_target_paths = list()
        str_kustomization_path = str()

        try:
            # test if the key to configure is even defined in input helmizer config
            list_kustomization_children = self.helmizer_config['kustomize'][key].get(list)

            str_kustomization_path = path.dirname(path.abspath(path.normpath(path.join(arguments.helmizer_config, self.helmizer_config['helmizer']['kustomization-directory'].get(str)))))

            if len(list_kustomization_children) > 0:
                for target_path in list_kustomization_children:
                    str_child_path = path.abspath(path.join(str_kustomization_path, target_path))

                    # walk directory
                    if path.isdir(str_child_path):
                        for (dirpath, _, filenames) in walk(str_child_path):
                            for filename in filenames:
                                list_target_paths.append(path.join(dirpath, filename))

                    # file
                    elif path.isfile(str_child_path):
                        list_target_paths.append(str_child_path)

                    # url
                    elif validate_url(str_child_path):
                        list_target_paths.append(str_child_path)

                # convert absolute paths into paths relative to the kustomization directory
                for final_target_path in list_target_paths:
                    list_final_target_paths.append(path.relpath(final_target_path, str_kustomization_path))

                # remove any ignored files
                try:
                    for ignore in self.helmizer_config['helmizer']['ignore'].get(list):
                        logging.debug(f'Removing ignored file from final list: {ignore}')
                        list_final_target_paths.remove(ignore)
                except ValueError:
                    pass
                except NotFoundError:
                    pass

                return list_final_target_paths

        except NotFoundError:
            logging.debug(f'key not found: {key}')
            pass
        except KeyError:
            logging.debug(f'key not found: {key}')
            pass
        except TypeError:
            pass


def run_subprocess(helmizer_config, arguments):
    subprocess_working_directory = path.dirname(path.abspath(path.normpath(arguments.helmizer_config)))

    logging.debug(f'Subprocess working directory: {subprocess_working_directory}')

    list_command_string = list()
    try:
        for config_command in helmizer_config['helmizer']['commandSequence']:
            # construct command(s)
            if config_command['command']:
                command = config_command['command'].get(str)
                if config_command['args']:
                    args = ' '.join(config_command['args'].get(list))  # combine list elements into space-delimited
                    list_command_string.append(f'{command} {args}')
                else:
                    list_command_string.append(f'{command}')

        # execute
        for command in list_command_string:
            if arguments.quiet:
                logging.debug(f"creating subprocess: \'{command}\'")
                subprocess.run(f'{command}', shell=True, check=True, stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL, text=True, cwd=subprocess_working_directory)
            else:
                logging.info(f"creating subprocess: \'{command}\'")
                subprocess.run(f'{command}', shell=True, check=True, text=True, cwd=subprocess_working_directory)

    except NotFoundError as e:
        pass


def init_arg_parser():
    try:
        parser = argparse.ArgumentParser(prog='helmizer', description='Helmizer', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
        args = parser.add_argument_group()
        args.add_argument('--debug', dest='debug', action='store_true', help='enable debug logging', default=False)
        args.add_argument('--dry-run', dest='dry_run', action='store_true', help='do not write to a file system', default=False)
        args.add_argument('--skip-commands', dest='skip_commands', action='store_true',
                         help='skip executing commandSequence, just generate kustomization file', default=False)
        args.add_argument('--quiet', '-q', dest='quiet', action='store_true', help='quiet output from subprocesses',
                         default=False)
        args.add_argument('--version', action='version', version='v0.8.0')
        args.add_argument('helmizer_config', action='store', type=str, help='path to helmizer config file')
        arguments = parser.parse_args()

        if arguments.quiet:
            logging.basicConfig(level=logging.INFO, datefmt=None, stream=None, format='[%(asctime)s %(levelname)s] %(message)s')
        if arguments.debug:
            logging.basicConfig(level=logging.DEBUG, datefmt=None, stream=stdout, format='[%(asctime)s %(levelname)s] %(message)s')
        else:
            logging.basicConfig(level=logging.INFO, datefmt=None, stream=stdout, format='[%(asctime)s %(levelname)s] %(message)s')

        return arguments
    except argparse.ArgumentError as e:
        logging.error('Error parsing arguments')
        raise e


def validate_helmizer_config_version(helmizer_config_version):
    # TODO actually validate it
    logging.debug(f'validating helmizer config version: {helmizer_config_version}')


def init_helmizer_config(arguments):
    str_helmizer_config_path = arguments.helmizer_config

    config = confuse.Configuration('helmizer', __name__)
    try:
        if str_helmizer_config_path:
            logging.debug(f'Trying helmizer config path from argument: {str_helmizer_config_path}')
            config.set_file(path.normpath(str_helmizer_config_path))
            logging.debug(f'parsed config: {config}')

    # no config file found. Give up
    except confuse.exceptions.ConfigReadError:
        logging.error(f'Unable to locate helmizer config. Path provided: {str_helmizer_config_path}')
        exit(1)

    try:
        validate_helmizer_config_version(config['helmizer']['version'].get(str))
    except KeyError:
        logging.debug('Unable to validate version')

    return config


def main():
    arguments = init_arg_parser()
    helmizer_config = init_helmizer_config(arguments)
    if not arguments.skip_commands:
        run_subprocess(helmizer_config, arguments)
    kustomization = Kustomization(helmizer_config, arguments)
    kustomization.render_template(arguments)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt or SystemExit:
        exit(1)
