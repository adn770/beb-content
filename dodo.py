import os


def task_pylint():
    return {
        'actions': ['pylint utils/*.py'],
        'clean': True
    }

def task_flake():
    return {
        'actions': ['flake8 --max-line-length 95 utils/*.py'],
        'clean': True
    }

