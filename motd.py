#!/usr/bin/python

import os
import re
import subprocess
import math
import random
import textwrap

def sh(cmd):
    return subprocess.check_output(cmd, shell=True).strip()

COLORS = {
    'bold': "\033[01m",
    'black': "\033[30m",
    'red': "\033[31m",
    'green': "\033[32m",
    'yellow': "\033[33m",
    'blue': "\033[34m",
    'purple': "\033[35m",
    'cyan': "\033[36m",
    'white': "\033[37m",
    'reset': "\033[0m",
    'system': "\033[38;5;120m",
}

def smartlen(line):
    """Calculate an idea of what length a line will really end up having."""
    line = line.replace("\t", ' '*4)
    for color in COLORS.iterkeys():
        line = line.replace(COLORS[color], '')
    return len(line)

def humanise(num):
    """Human-readable size conversion."""
    for x in ['bytes','KB','MB','GB','TB']:
        if num < 1024.0:
            return "%3.1f%s" % (num, x)
        num /= 1024.0


def column_display(rows, num_columns=2):
    """Horrible fluid column layout code ahoy!"""
    columns = []

    column = []
    for row in rows:
        column.append(row)
        if len(column) >= math.floor(float(len(rows))/num_columns):
            columns.append(column)
            column = []
    if len(column) > 0: columns.append(column)

    col_texts = []
    for col in columns:
        coltext = []
        max_keylen = max([len(row[0]) for row in col])
        for row in col:
            padding = ' '*(max_keylen-len(row[0]))
            coltext.append("%s: %s%s" % (row[0], padding, row[1]))
        col_texts.append(coltext)

    result = ""
    for i in range(len(col_texts[0])):
        line = ""

        for j, coltext in enumerate(col_texts):
            if i < len(coltext):
                if j > 0:
                    max_vallen = max([len(row[1]) for row in columns[j-1]])
                    vallen = len(columns[j-1][i][1])
                    line += "\t"*max([1, int(math.floor(float(max_vallen-vallen)/4))])
                line += coltext[i]
        result += line + "\n"

    return result

def center_by(width, uncentered):
    result = ""
    lines = uncentered.split("\n")
    length = max([smartlen(line) for line in lines])
    for line in lines:
        result += ' '*int((width-length)/2) + line + "\n"
    return result


def colored(col, s):
    return COLORS[col] + s + COLORS['reset']

def sysinfo():
    raw_loadavg = sh("cat /proc/loadavg").split()
    load = {
        '1min': float(raw_loadavg[0]),
        '5min': float(raw_loadavg[1]),
        '15min': float(raw_loadavg[2])
    }

    raw_home = sh("df -P /home | tail -1").split()
    raw_home_human = sh("df -Ph /home | tail -1").split()

    home = {
        'used': int(raw_home[2]),
        'total': int(raw_home[1]),
        'used_human': raw_home_human[2],
        'total_human': raw_home_human[1],
    }

    home['ratio'] = float(home['used'])/home['total']

    raw_free = sh("free -b").split("\n")
    raw_mem = raw_free[1].split()
    raw_swap = raw_free[3].split()

    memory = {
        'used': int(raw_mem[2])-int(raw_mem[6]),
        'total': int(raw_mem[1])
    }

    memory['ratio'] = float(memory['used'])/memory['total']

    swap = {
        'used': int(raw_swap[2]),
        'total': int(raw_swap[1])
    }

    swap['ratio'] = float(swap['used'])/swap['total']

    process_count = int(sh("ps aux|wc -l"))-1

    raw_eth0 = sh("ifconfig eth0")
    eth0 = {
        'ipaddr': re.search(r'inet addr:(\S+)', raw_eth0).group(1)
    }

    rows = []

    raw_passwd = sh("getent passwd").split("\n")

    userlist = []
    for line in raw_passwd:
        spl = line.split(':')
        if int(spl[2]) > 1000:
            userlist.append(spl[0])

    users = {
        'total': len(userlist),
        'active': len(set(sh("users").split()))
    }

    raw_uptime = sh("uptime")
    uptime = raw_uptime.split(',')[0].split('up')[1].strip()


    if load['1min'] < 0.4: load['color'] = 'green'
    elif load['1min'] < 0.8: load['color'] = 'yellow'
    else: load['color'] = 'red'

    rows.append(['System Load', colored(load['color'], str(load['1min']))])

    if home['ratio'] < 0.4: home['color'] = 'green'
    elif home['ratio'] < 0.8: home['color'] = 'yellow'
    else: home['color'] = 'red'

    rows.append(["/home Usage", colored(home['color'],
            "%d%% of %s" % (home['ratio']*100, home['total_human']))])

    if memory['ratio'] < 0.4: memory['color'] = 'green'
    elif memory['ratio'] < 0.8: memory['color'] = 'yellow'
    else: memory['color'] = 'red'

    rows.append(['Memory Usage', colored(memory['color'], \
            "%d%% of %s" % (memory['ratio']*100, humanise(memory['total'])))])

    if swap['ratio'] < 0.4: swap['color'] = 'green'
    elif swap['ratio'] < 0.8: swap['color'] = 'yellow'
    else: swap['color'] = 'red'

    rows.append(["Swap Usage", colored(swap['color'], "%d%%" % (swap['ratio']*100))])

    rows.append(['Total Users', str(users['total'])])
    rows.append(['Active Users', str(users['active'])])
    rows.append(["Process Count", str(process_count)])
    rows.append(['Uptime', uptime])

    return rows

if __name__ == "__main__":
    banner = colored('system', open("/etc/motd_banner").read())
    banner_length = max([smartlen(line) for line in banner.split("\n")])
    info = center_by(banner_length, column_display(sysinfo(), num_columns=2))
    #quotes = open(os.path.join(os.path.dirname(__file__), 'quotes')).read().split("%\n")
    #quote = center_by(banner_length, random.choice(quotes))

    output = banner + "\n" + info


    excerpts_path = os.path.join(os.path.dirname(__file__), 'excerpts')
    if os.path.exists(excerpts_path):
        excerpt = random.choice(open(excerpts_path).read().split("%\n"))
        title = excerpt.split("\n")[0]
        content = "\n".join(excerpt.split("\n")[1:])
        wrapped = textwrap.fill(content, math.ceil(banner_length*0.8))
        output += center_by(banner_length, title)
        output += center_by(banner_length, wrapped)

    print output
