#!/usr/bin/env python
import sys, os
import argparse
import gettext
from datetime import date, datetime
import yaml
from yaml import Loader, Dumper

locales_dir = os.path.realpath(sys.argv[0]).replace('/src/crops.py', '/locales')
lang_translations = gettext.translation('base', localedir=locales_dir)
lang_translations.install()
_ = lang_translations.gettext

VERBOSE = False
PLANT_STAGES = ["planted", "germination", "seedling", "cutting", "vegetation", "budding", "flowering", "ripening", "drying", "curing", "harvested"]
PLANT_STAGES_LC = [_("planted"), _("germination"), _("seedling"), _("cutting"), _("vegetation"), _("budding"), _("flowering"), _("ripening"), _("drying"), _("curing"), _("harvested")]

def vprint(*args):
    if VERBOSE: print('[crops]', *args)


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
        if self.args.command == 'info':
            self.show_info(self.args.water, self.args.stage, self.args.age)
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
        # NOTE: Init an empty event dict to avoid AttributeError (saving changes is not needed)
        if len(self.crop_data) == 1:
            self.crop_data.append({})
        elif self.crop_data[self.FILE_EVENTS] is None:
            self.crop_data[self.FILE_EVENTS] = {}

    @property
    def crop_info(self):
        return self.crop_data[self.FILE_INFO]
    
    @property
    def crop_events(self):
        return self.crop_data[self.FILE_EVENTS]

    def show_info(self, show_water=False, show_stage=False, show_age=False):
        no_command = True
        events_data = self.crop_events
        info_data = self.crop_info
        if show_stage:
            no_command = False
            stage = None
            stage_date = None
            for event_date in reversed(events_data.keys()):
                for event_time in reversed(events_data[event_date].keys()):
                    for event in events_data[event_date][event_time]:
                        if type(event) is dict and 'stage' in event:
                            stage = event['stage']
                            stage_date = event_date
                        if stage is not None: break
                    if stage is not None: break
                if stage is not None: break
            if stage is None:
                stage = 'planted'
                stage_date = info_data['planted']
            stage_date = stage_date if type(stage_date) == date else stage_date.date()
            diff = self.now_date - stage_date
            print(_('Current {0} stage: {1} (since {2}, {3} days ago).').format(info_data['name'], stage, stage_date.strftime(r'%Y-%m-%d'), diff.days))
        if show_water:
            no_command = False
            water = None
            water_date = None
            for event_date in reversed(events_data.keys()):
                for event_time in reversed(events_data[event_date].keys()):
                    for event in events_data[event_date][event_time]:
                        if type(event) is dict and 'water' in event:
                            water = event['water']
                            water_date = event_date
                        elif type(event) is str and event == 'water':
                            water = event
                            water_date = event_date
                        if water is not None: break
                    if water is not None: break
                if water is not None: break
            if water is None:
                print(_("{0} was never watered.").format(info_data['name']))
            else:
                diff = self.now_date - water_date
                if diff.days > 0:
                    print(_("{0} was watered {1}, {2} days ago.").format(info_data['name'], water_date.strftime('%d %B (%a)'), abs(diff.days)))
                else:
                    print(_("{0} was watered today.").format(info_data['name'], diff.days))
        if show_age:
            no_command = False
            planted_date = info_data['planted']
            planted_date = planted_date if type(planted_date) == date else planted_date.date()
            diff = self.now_date - planted_date
            print(_("{0} has been planted for {1} days.").format(info_data['name'].capitalize(), abs(diff.days)))
        if no_command:
            print("[ {0} ]".format(self.current_file))
            print("== Crop Info ==")
            print(yaml.safe_dump(info_data, sort_keys=False))
            print("==Crop Events==")
            if len(events_data) > 0:
                print(yaml.safe_dump(events_data))
            else:
                print(_("No events added yet."))

    def water(self, additives=None, notes=None):
        info_data = self.crop_info
        template = _("[{0}] Watering {1}.")
        entry_data = None
        if additives is not None:
            entry_data = { 'water': { 'additives': additives } }
            template = _("[{0}] Watering {1} with {2}.").format('{0}', '{1}', ', '.join(additives))
        if notes is not None:
            if entry_data is None:
               entry_data = { 'water': { 'notes': notes } }
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


def new_crop(args, output):
    from bullet import VerticalPrompt, Input, Numbers, Bullet
    PROMPT = ": "
    RESULT_NAME, RESULT_NUM, RESULT_CULTIVAR, RESULT_STAGE, RESULT_SRC, RESULT_NOTES = range(6)
    cli = VerticalPrompt(
        [
            Input(_("Plant name")+PROMPT),
            Numbers(_("Number of plants")+PROMPT, type=int),
            Input(_("Plant cultivar")+PROMPT, default=_("optional")),
            Bullet(_("Initial stage"), choices=PLANT_STAGES_LC),
            Input(_("Source")+PROMPT, default=_("seeds")),
            Input(_("Notes")+PROMPT, default=_("optional")),
        ],
        spacing=1
    )
    result = cli.launch()

    crop_data = {
        'name': result[RESULT_NAME][1],
        'plants': result[RESULT_NUM][1],
        'cultivar': result[RESULT_CULTIVAR][1] if result[RESULT_CULTIVAR][1] != _("optional") else _("{0} (unknown)").format(result[RESULT_NAME][1]),
        'planted': datetime.now(),
        'source': result[RESULT_SRC][1],
        'notes': None if result[RESULT_NOTES][1] == _("optional") else result[RESULT_NOTES][1]
    }
    new_stage = None
    if result[RESULT_STAGE][1] != _("planted"):
        new_stage = PLANT_STAGES[PLANT_STAGES_LC.index(result[RESULT_STAGE][1])]
    path = crop_data['name'].replace(' ', '') if output is None else output
    path = (path+'.crop').replace('.crop.crop', '.crop')
    if os.path.exists(path):
        print("File already exists. Aborting!", file=sys.stderr)
    else:
        yaml.safe_dump(crop_data, open(path, 'w'), allow_unicode=True)
        if new_stage is not None:
            main(['stage', new_stage, path])
        print("New crop saved to: "+path)

def main(argv):
    args_parser = argparse.ArgumentParser(prog="crops")
    args_parser.add_argument('-v', action='store_true')

    sub_parser = args_parser.add_subparsers(dest="command")
    new_args = sub_parser.add_parser('new')

    info_args = sub_parser.add_parser('info')
    info_args.add_argument('-s', '--stage', action='store_true')
    info_args.add_argument('-w', '--water', action='store_true')
    info_args.add_argument('-a', '--age', action='store_true')

    water_args = sub_parser.add_parser('water')
    water_args.add_argument('-a', '--additives', type=str, action='append')
    water_args.add_argument('-n', '--notes', type=str)

    feed_args = sub_parser.add_parser('feed')
    feed_args.add_argument('-n', '--notes', type=str)

    stage_args = sub_parser.add_parser('stage')
    stage_args.add_argument('stage', choices=PLANT_STAGES[1:])

    args, files = args_parser.parse_known_args(argv)
    global VERBOSE
    VERBOSE = args.v

    vprint('command:', args.command)
    vprint('crops:', files)

    if args.command == 'new':
        new_crop(args, files[0] if len(files) > 0 else None)
    elif len(files) <= 0:
        args_parser.print_help()
    else:
        command_processor = CropsCommandProcessor(args)
        for crop in files:
            command_processor.execute(crop)


if __name__ == '__main__':
    main(sys.argv[1:])
