#!/usr/bin/python3
import sys, os
import argparse
import gettext
from datetime import datetime
import yaml
from yaml import Loader, Dumper

locales_dir = os.path.realpath(sys.argv[0]).replace('/src/crops.py', '/locales')
lang_translations = gettext.translation('base', localedir=locales_dir)
lang_translations.install()
_ = lang_translations.gettext

argsp = argparse.ArgumentParser(prog="crops")
argsp.add_argument('-v', action='store_true')

subp = argsp.add_subparsers(dest="command")
newp = subp.add_parser('new')

showp = subp.add_parser('show')
showp.add_argument('-s', '--stage', action='store_true')
showp.add_argument('-w', '--water', action='store_true')

waterp = subp.add_parser('water')
waterp.add_argument('-a', '--additives', type=str, action='append')
waterp.add_argument('-n', '--notes', type=str)

feedp = subp.add_parser('feed')
feedp.add_argument('-n', '--notes', type=str)

stagep = subp.add_parser('stage')
stagep.add_argument('stage', choices=["emerging", "vegetation", "reproduction", "harvested"])

args, files = argsp.parse_known_args()

VERBOSE = args.v

def vprint(*args):
    if VERBOSE: print('[crops]', *args)

def new_crop(args, output):
    pass

class CropsCommandProcessor(object):
    FILE_INFO, FILE_EVENTS = 0, 1
    crop_data = None
    current_file = None

    def __init__(self, args):
        self.now = datetime.now()
        self.args = args

    def execute(self, file):
        self.current_file = file
        self.load_crop_data()
        if self.args.command == 'show':
            self.show_info(self.args.water, self.args.stage)
        elif self.args.command == 'water':
            self.water(self.args.additives, self.args.notes)
            self.save_changes()
        elif self.args.command == 'stage':
            self.change_stage(self.args.stage)
            self.save_changes()

    @property
    def now_date(self):
        return self.now.date()

    @property
    def now_time(self):
        return self.now.time()

    @property
    def now_formatted(self):
        return self.now.strftime(r'%Y-%m-%d %H:%M')
    
    @property
    def now_time_formatted(self):
        return self.now.strftime(r'%Hh%M')
    
    def load_crop_data(self):
        self.crop_data = list(yaml.safe_load_all(open(self.current_file)))

    @property
    def crop_info(self):
        return self.crop_data[self.FILE_INFO]
    
    @property
    def crop_events(self):
        return self.crop_data[self.FILE_EVENTS]

    def show_info(self, show_water=False, show_stage=False):
        no_command = True
        events_data = self.crop_events
        info_data = self.crop_info
        if show_stage:
            no_command = False
            stage = None
            stage_date = None
            for date in reversed(events_data.keys()):
                for time in reversed(events_data[date].keys()):
                    for event in events_data[date][time]:
                        if type(event) is dict and 'stage' in event:
                            stage = event['stage']
                            stage_date = date
                        if stage is not None: break
                    if stage is not None: break
                if stage is not None: break
            if stage is None:
                stage = 'planted'
                stage_date = info_data['planted']
            print(_('Current {0} stage: {1} (since {2}).').format(info_data['name'], stage, stage_date.strftime(r'%Y-%m-%d %H:%M')))
        if show_water:
            no_command = False
            water = None
            water_date = None
            for date in reversed(events_data.keys()):
                for time in reversed(events_data[date].keys()):
                    for event in events_data[date][time]:
                        if type(event) is dict and 'water' in event:
                            water = event['water']
                            water_date = date
                        elif type(event) is str and event == 'water':
                            water = event
                            water_date = date
                        if water is not None: break
                    if water is not None: break
                if water is not None: break
            if water is None:
                print(_("{0} was never watered.").format(info_data['name']))
            else:
                diff = self.now_date - water_date
                if diff.days > 0:
                    print(_("{0} was watered {1} days ago.").format(info_data['name'], diff.days))
                else:
                    print(_("{0} was watered today.").format(info_data['name'], diff.days))
        if no_command:
            print("[ {0} ]".format(self.current_file))
            print("== Crop Info ==")
            print(yaml.safe_dump(info_data, sort_keys=False))
            print("==Crop Events==")
            print(yaml.safe_dump(events_data))
    
    def water(self, additives=None, notes=None):
        info_data = self.crop_info
        template = _("[{0}] Watering {1}.")
        entry_data = None
        if additives is not None:
            entry_data = { 'water': { 'additives': additives } }
            template = _("[{0}] Watering {1} with {2}.").format('{0}', '{1}', ', '.join(additives))
        if notes is not None:
            if entry_data is None:
               entry_data  = { 'water': { 'notes': notes } }
            else:
                entry_data['water']['notes'] = notes
        if entry_data is None:
            entry_data = 'water'
        self.add_entry(entry_data)
        print(template.format(self.now_formatted, info_data['name']))

    def change_stage(self, stage):
        info_data = self.crop_info
        entry_data = { 'stage': stage }
        self.add_entry(entry_data)
        print(_('[{0}] Stage of {1} set to {2}.').format(self.now_formatted, info_data['name'], stage))

    def add_entry(self, data):
        date_key = self.now_date
        time_key = self.now_time_formatted
        events = self.crop_events
        if not date_key in events:
            events[date_key] = {}
        if not time_key in events[date_key]:
            events[date_key][time_key] = []
        now_events = events[date_key][time_key]
        now_events.append(data)
    
    def save_changes(self):
        yaml.safe_dump_all(self.crop_data, open(self.current_file, 'w'), allow_unicode=True)

if __name__ == '__main__':
    vprint('command:', args.command)
    vprint('crops:', files)
    if len(files) <= 0:
        argsp.print_help()
    elif args.command == 'new':
        pass
    else:
        command_processor = CropsCommandProcessor(args)
        for crop in files:
            command_processor.execute(crop)
