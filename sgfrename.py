import argparse
from datetime import datetime
import glob
import os
import re
import sys
from string import Template

default_name_format = '$date - $location - $blackname [$blackrank] - $whitename [$whiterank] - $result'

servers = {
    'OGS': {
        'tag': 'PC',
        'identifier': 'OGS:'
    },
    'KGS': {
        'tag': 'PC',
        'identifier': 'The KGS Go Server'
    },
    'Tygem': {
        'tag': 'PC',
        'identifier': 'Tygem'
    },
    'WBaduk': {
        'tag': 'PC',
        'identifier': 'wbaduk'
    },
    'CyberOro': {
        'tag': 'US',
        'identifier': 'www.cyberoro.com'
    },
    'IGS': {
        'tag': 'PC',
        'identifier': 'IGS:'
    },
    'Fox': {
        'tag': 'AP',
        'identifier': 'foxwq',
    },
    'DGS': {
        'tag': 'PC',
        'identifier': 'Dragon Go Server'
    },
    'GoShrine': {
        'tag': 'PC',
        'identifier': 'GoShrine'
    },
    'INGO': {
        'tag': 'PC',
        'identifier': 'Played on INGO'
    },
    'LankeWeiqi': {
        'tag': 'PC',
        'identifier': '烂柯围棋网',
    }
}

translations = {
    'ranks': {
        r'(\d+)段': r'\1d',
        r'(\d+)级': r'\1k',
        r'[dp](\d)[pd]': r'\1p',
        r'^\?$': 'unknown-rank'
    },
    'results': {
        '没有结果': 'Unknown',
        '黑中盘胜。': 'B+Resign',
        '白中盘胜。': 'W+Resign',
        '白方强退告负。': 'B+Forfeit',
        '黑方强退告负。': 'W+Forfeit',
        r'黑胜(\d+(\.5)?)目': r'B+\1',
        r'白胜(\d+(\.5)?)目': r'W+\1',
        '白方超时负': 'B+Time',
        '黑方超时负': 'W+Time',
        '和棋。': 'Draw',
        r'^([BW])\+T$': r'\1+Time',
        r'^([BW])\+F$': r'\1+Forfeit',
        r'^([BW])\+R$': r'\1+Resign',
        r'[WB][a-z]+ (\d+[\.5]*)': r'W+\1',
        r'[WB][a-z]+ w[oi]ns? by res': r'W+Resign'
    }
}

def translate(value, dictionary):
    for foreign, translation in dictionary.items():
        match = re.search(foreign, value, re.IGNORECASE)
        if match:
            return match.expand(translation)
    return value

def find_prop(data, prop):
    reg = r'{0}\[([^]\\]*(?:\\.[^]\\]*)*)\]'.format(prop)
    matches = re.findall(reg, data)
    return matches

def find_location(data):
    for server, info in servers.items():
        props = find_prop(data, info['tag'])
        for value in props:
            if value.startswith(info['identifier']):
                return server
    return None

def list_get(list, index, default):
  try:
    return list[index]
  except IndexError:
    return default

def parse_date(date):
    date_reg = r'(\d{4})[\D]*(\d\d|\d)[\D]*(\d{1,2})[\D]*((\d{1,2})[\D]+(\d\d)[\-\: ]*(\d\d)?)?'
    match = re.search(date_reg, date)
    if match:
        template = r'\1-\2-\3 \5.\6'
        datetime_format = '%Y-%m-%d %H.%M'
        if not match.group(4):
            template = r'\1-\2-\3'
            datetime_format = '%Y-%m-%d'
        datetime_object = datetime.strptime(match.expand(template), datetime_format)
        return datetime_object.strftime(datetime_format)

    return date

def get_game_info(data):
    game_info = {}

    game_info['date'] = parse_date(list_get(find_prop(data, 'DT'), 0, 'unknown-date'))

    game_info['blackname'] = list_get(find_prop(data, 'PB'), 0, 'unknown-player').strip()
    game_info['whitename'] = list_get(find_prop(data, 'PW'), 0, 'unknown-player').strip()

    blackrank_unprocessed = list_get(find_prop(data, 'BR'), 0, 'unknown-rank')
    game_info['blackrank'] = translate(blackrank_unprocessed, translations['ranks'])

    whiterank_unprocessed = list_get(find_prop(data, 'WR'), 0, 'unknown-rank')
    game_info['whiterank'] = translate(whiterank_unprocessed, translations['ranks'])

    game_info['location'] = find_location(data)

    result_unprocessed = list_get(find_prop(data, 'RE'), 0, 'unknown-result') 
    game_info['result'] = translate(result_unprocessed, translations['results'])

    return game_info

def main():
    argument_parser = argparse.ArgumentParser()
    argument_parser.add_argument("-r", "--recursive", action='store_true', help="Search folders recursively")
    argument_parser.add_argument("-f", "--format", default=default_name_format, help="Renaming format string. Variables: $date, $location, $result, $blackname, $whitename, $blackrank, $whiterank")

    options = vars(argument_parser.parse_args())

    template = Template(options['format'])

    for file in glob.glob('*.sgf', recursive=options['recursive']):
        with open(file, 'r', encoding='utf-8') as f:
            print(file , ': ')
            try:
                data = f.read()
            except:
                print('Could not read ' , file)
                continue

        game_info = get_game_info(data)

        new_filename = re.sub(r'[\/\\;,><&\*:%=@!#\^\(\)\|\?]', '', template.substitute(game_info))
        new_filename += '{}.sgf'

        counter = ''
        if os.path.isfile(new_filename):
            counter = 1
            while os.path.isfile(new_filename.format(counter)):
                counter += 1
        os.rename(file, new_filename.format(counter))

if __name__ == "__main__":
    main()
