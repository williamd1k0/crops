#!/usr/bin/python3
from datetime import datetime
import argparse
import yaml
from yaml import Loader, Dumper

argsp = argparse.ArgumentParser(prog="crops")
argsp.add_argument_group()
subp = argsp.add_subparsers(dest="command")
newp = subp.add_parser('new')

showp = subp.add_parser('show')
showp.add_argument('-s', '--stage', action='store_true')
showp.add_argument('-w', '--water', action='store_true')

waterp = subp.add_parser('water')
waterp.add_argument('-a', '--additives', type=str)
waterp.add_argument('-n', '--notes', type=str)

stagep = subp.add_parser('stage')
stagep.add_argument('stage', choices=["emerging", "vegetation", "reproduction", "harvested"])

argsp.add_argument("crop", type=str, nargs='+')
argsp.add_argument("-v", action='store_true')


args = argsp.parse_args()


FILE_INFO, FILE_EVENTS = 0, 1
VERBOSE = args.v

def vprint(*args):
    if VERBOSE: print('[crops]', *args)

vprint('command:', args.command)
vprint('crops:', args.crop)

if args.command == 'new':
    pass
else:
    now = datetime.now()
    now_date = now.date()
    now_time = now.time()
    now_str = now.strftime(r'%Y-%m-%d %H:%M')
    for crop in args.crop:
        crop_data = list(yaml.safe_load_all(open(crop)))
        info_data = crop_data[FILE_INFO]
        events_data :dict = crop_data[FILE_EVENTS]
        vprint(info_data)
        vprint(events_data)
        if args.command == 'show':
            no_command = True
            if args.stage:
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
                print('Current {} stage: {} (since {}).'.format(info_data['name'], stage, stage_date.strftime(r'%Y-%m-%d %H:%M')))
            if args.water:
                no_command = False
                water = None
                water_date = None
                for date in reversed(events_data.keys()):
                    for time in reversed(events_data[date].keys()):
                        for event in events_data[date][time]:
                            if type(event) is dict and 'water' in event:
                                water = event['water']
                                water_date = date
                            if water is not None: break
                        if water is not None: break
                    if water is not None: break
                if water is None:
                    print("{} was never watered.".format(info_data['name']))
                else:
                    diff = now_date - water_date
                    print("{} was watered {} days ago.".format(info_data['name'], diff.days))
            if no_command:
                print("== Crop Info ==")
                print(yaml.safe_dump(info_data, sort_keys=False))
                print("==Crop Events==")
                print(yaml.safe_dump(events_data))
        elif args.command == 'stage':
            stage = args.stage
            print('[{}] Stage of {} set to {}.'.format(now_str, info_data['name'], stage))