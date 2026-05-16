# SPDX-License-Identifier: Apache-2.0

'''bflb_test_command.py
West command for controlling a test rig.
'''

import json
import os
import shutil
import subprocess
import sys
import time
import yaml
from west.commands import ExtensionCommandError
from west.commands import WestCommand

REPO_URL = 'https://github.com/josuah/zephyr_bflb_test/'
ZEPHYR_URL = 'https://github.com/zephyrproject-rtos/zephyr'

class BflbTestCommand(WestCommand):
    '''Class for the bflb-test command'''

    def __init__(self):
        super().__init__(
            'bflb-test',
            'Control a test rig for BouffaloLab testing',
            'Manage a test rig and test results. See the README for an example.'
        )
        self.testsuites = []

    def do_add_parser(self, parser_adder):
        parser = parser_adder.add_parser(
            self.name, help=self.help, description=self.description
        )

        subparsers = parser.add_subparsers(dest='subcmd')

        parser_init = subparsers.add_parser(
            'init', help='Initialize a new test rig'
        )
        parser_init.add_argument('name', help='name of the test rig to initialize')

        parser_set = subparsers.add_parser(
            'set', help='Assign a serial console to a board into the hardware map'
        )
        parser_set.add_argument('serial', help='path to the serial console (i.e. /dev/ttyACM0)')
        parser_set.add_argument('board', help='board name to add (i.e. ai_m61_32s_kit)')

        parser_del = subparsers.add_parser(
            'del', help='Delete a board from the test rig'
        )
        parser_del.add_argument('serial', help='board name to delete (i.e. ai_m61_32s_kit)')

        parser_list = subparsers.add_parser(
            'list', help='List the boards from the test rig'
        )

        parser_run = subparsers.add_parser(
            'run', help='Run twister with default arguments and extra; given arguments'
        )
        parser_run.add_argument('extra', help='extra args i.e. -- -T samples/hello_world', nargs='*')

        parser_html = subparsers.add_parser(
            'html', help='Generate HTML report of all the tests currently stored'
        )

        parser_push = subparsers.add_parser(
            'push', help='Push the current results using git so they can be visible online'
        )

        return parser

    def do_run(self, args, _):
        if args.subcmd is None:
            self.parser.print_help()
            sys.exit(1)
        subcmd = getattr(self, 'subcmd_' + args.subcmd)
        subcmd(args)

    def error(self, msg):
        print(f'error: {msg}')
        sys.exit(1)

    def run_cmd(self, *args):
        print('$ ' + ' '.join(args))
        return subprocess.run(args)

    def git(self, *args):
        self.run_cmd('git', '-C', self.repo_path('.'), *args).check_returncode()

    def rig_name(self):
        name = self.config.get('bflb-test.rig')
        if name is None:
            self.error('Call "init" first to set the rig name')
        return name

    def repo_path(self, path):
        return os.path.realpath(os.path.dirname(__file__) + '/../' + path)

    # hwmap

    def hwmap_path(self):
        return self.repo_path('rigs/' + self.rig_name() + '.hwmap.yml')

    def hwmap_yaml(self):
        with open(self.hwmap_path(), 'a+') as f:
            pass
        with open(self.hwmap_path(), 'r') as f:
            return yaml.safe_from(f)

    def hwmap_list(self, hwmap):
        for row in hwmap:
            status = 'ok' if os.path.exists(row['serial']) else 'off'
            print(f'  {status:3} {row["id"]} {row["platform"]}')

    def hwmap_del(self, hwmap, id):
        return [x for x in hwmap if x['id'] != id]

    def hwmap_save(self, hwmap):
        with open(self.hwmap_path(), 'w') as f:
            yaml.dump(hwmap, f, default_flow_style=False)

    def read_results(self):
        rigs = os.listdir(self.repo_path('results'))

        for rig in rigs:
            for json_file in os.listdir(self.repo_path('results/' + rig)):
                json_path = self.repo_path('results/' + rig + '/' + json_file)

                # Build a flat array of dicts out of the nested JSON structs
                with open(json_path) as f:
                    json_data = json.load(f)
                    for testsuite in json_data['testsuites']:
                        version = json_data['environment']['zephyr_version']
                        testsuite['commit_hash'] = version[version.index('g') + 1:]
                        testsuite['commit_date'] = json_data['environment']['commit_date']
                        testsuite['rig'] = rig
                        self.testsuites.append(testsuite)

    def fields(self, key, selection=None):
        '''Sorted set of all possible values for "testsuite[key]"'''
        return sorted(set(([x[key] for x in selection or self.testsuites])))

    def select(self, key, value, selection=None):
        '''Select a subset of testsuites results for which "testsuite[key] == value"'''
        return [x for x in selection or self.testsuites if x[key] == value]
    # html

    def html_dump_file(self, dst_file, src_path):
        with open(src_path, 'r') as src_file:
            dst_file.write(src_file.read())

    def html_table_beg(self, f, row):
        f.write('<table><thead><tr>')
        for td in row:
            f.write(f'<td>{td}</td>')
        f.write('</tr></thead><tbody>\n')

    def html_table_row(self, f, row):
        f.write(' <tr>')
        for td in row:
            f.write(f'<td>{td}</td>')
        f.write('</tr>\n')

    def html_table_body(self, f):
        for date in self.fields('commit_date'):
            date_selection = self.select('commit_date', date)
            hash = date_selection[0]['commit_hash']

            tooltip = f'<span class="tooltip">{date}</span>'
            first_col = f'<a href="{ZEPHYR_URL}/commit/{hash}">{hash} {tooltip}</a>'

            table_row = [first_col]

            # Table row with one column per test
            for name in self.fields('name'):
                date_name_selection = self.select('name', name, selection=date_selection)
                if name not in self.fields('name', selection=date_name_selection):
                    table_row.append('-')
                    continue

                # Find number of different boards that succeeded this test
                boards = self.fields('platform')
                num_passing = 0
                num_total = len(boards)
                for board in boards:
                    selection = date_name_selection
                    selection = self.select('platform', board, selection=selection)
                    selection = self.select('status', 'passed', selection=selection)
                    if selection is not None:
                        num_passing += 1

                table_row.append(f'<a href="#{hash}_{name}">{num_passing}/{num_total}</a>')

            self.html_table_row(f, table_row)

            # Table row with details for each execution
            for name in self.fields('name'):
                date_name_selection = self.select('name', name, selection=date_selection)
                if name not in self.fields('name', selection=date_name_selection):
                    continue

                f.write(f' <tr id="{hash}_{name}" class="details"><td colspan=99><ul>\n')
                for testsuite in date_name_selection:
                    f.write(f'  <li><code>{testsuite}</code></li>\n')
                f.write(' </ul></td></tr>\n')

    def html_table_end(self, f):
        f.write('</tbody></table>\n')

    # subcmd

    def subcmd_init(self, args):
        self.config.set('bflb-test.rig', args.name)
        print(f'Test rig name set to "{args.name}" in {self.config._local_path}')

    def subcmd_del(self, args):
        hwmap = self.hwmap_yaml() or []
        hwmap = self.hwmap_del(hwmap, args.serial)
        self.hwmap_save(hwmap)
        self.hwmap_list(hwmap)

    def subcmd_set(self, args):
        if not os.path.exists(args.serial):
            self.error(f'{args.serial} serial console not found')
        hwmap = self.hwmap_yaml() or []
        hwmap = self.hwmap_del(hwmap, args.serial)
        hwmap.extend([{
            'connected': True,
            'flash_before': True,
            'id': args.serial,
            'notes': 'generated by "west bflb-test" command',
            'platform': args.board,
            'product': args.board,
            'runner': 'bflb_mcu_tool',
            'runner_params': [f'--dev-id={args.serial}'],
            'serial': args.serial,
        }])
        self.hwmap_save(hwmap)
        self.hwmap_list(hwmap)

    def subcmd_list(self, args):
        hwmap = self.hwmap_yaml() or []
        self.hwmap_list(hwmap)

    def subcmd_run(self, args):
        result = self.run_cmd(
            'west', 'twister', '--device-testing', '--hardware-map', self.hwmap_path(), *args.extra
        )

        dir = self.repo_path(f'results/{self.rig_name()}')
        filename = time.strftime('twister.%s.json')

        os.makedirs(dir, exist_ok=True)

        shutil.copyfile('twister-out/twister.json', dir + '/' + filename)

    def subcmd_push(self, args):
        self.git('add', '.')
        self.git('commit', '-m', f'publish results for {self.rig_name()}')
        self.git('pull', '--rebase')
        self.git('push', 'origin')

    def subcmd_html(self, args):
        self.read_results()

        os.makedirs('build', exist_ok=True)

        with open('build/index.html', 'w+') as f:
            self.html_dump_file(f, self.repo_path('docs/page_header.html'));
            self.html_table_beg(f, ('commit', *self.fields('name')))
            self.html_table_body(f)
            self.html_table_end(f)
            self.html_dump_file(f, self.repo_path('docs/page_footer.html'));

        shutil.copyfile(self.repo_path('docs/style.css'), 'build/style.css')
