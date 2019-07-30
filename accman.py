#!/usr/bin/python3

from accagg.passwordmanager import PasswordManager
import inquirer
import inquirer.themes

p = PasswordManager()

theme = inquirer.themes.load_theme_from_dict({
    'Checkbox': {
        'selected_icon': '[*]',
        'unselected_icon': '[ ]',
    }})

q = [
    inquirer.Checkbox('enable',
                      message="What are you interested in?",
                      choices=p.list(),
                      default=[i for i in p.list() if not 'disabled' in p.get(i)]),
]

answer = inquirer.prompt(q, theme=theme)

for i in p.list():
    if i in answer['enable']:
        p.enable(i)
    else:
        p.disable(i)

p.store()
