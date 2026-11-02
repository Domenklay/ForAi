# -*- coding: utf-8 -*-
import os
import py_compile
import shutil
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC = ROOT / 'src'
BUILD = ROOT / 'build'
DIST = ROOT / 'dist'
VERSION = '0.2.0'
MOD_BASENAME = 'DeepRelationships_v{}'.format(VERSION)
SCRIPT_NAME = MOD_BASENAME + '.ts4script'
USER_ZIP_NAME = MOD_BASENAME + '_INSTALL.zip'
EXPECTED_MAGIC = bytes.fromhex('420d0d0a')


def clean():
    for path in (BUILD, DIST):
        if path.exists():
            shutil.rmtree(str(path))
        path.mkdir(parents=True, exist_ok=True)


def compile_script():
    compiled = BUILD / 'compiled'
    compiled.mkdir(parents=True, exist_ok=True)
    source = SRC / 'deep_relationships.py'
    target = compiled / 'deep_relationships.pyc'
    py_compile.compile(str(source), cfile=str(target), doraise=True)
    return target


def verify_python37(pyc_path):
    data = pyc_path.read_bytes()
    magic = data[:4]
    if magic != EXPECTED_MAGIC:
        raise RuntimeError('Unexpected pyc magic for {}: {} (expected {})'.format(
            pyc_path.name, magic.hex(), EXPECTED_MAGIC.hex()))
    return magic.hex()


def make_ts4script(pyc_path):
    output = DIST / SCRIPT_NAME
    with zipfile.ZipFile(str(output), 'w', compression=zipfile.ZIP_DEFLATED) as archive:
        archive.write(str(pyc_path), arcname='deep_relationships.pyc')
    return output


def make_readme():
    text = '''ГЛУБОКИЕ ОТНОШЕНИЯ — v0.2.0\n\nСовместимость: The Sims 4 PC 1.127.x, DX11.\nЭто отдельный мод с нуля. Предыдущие семейные моды ему не нужны.\n\nВАЖНО\nПеред установкой удалите ВСЕ старые DeepRelationships_v0.1.x.ts4script. Одновременно должна находиться только версия v0.2.0.\n\nУСТАНОВКА\n1. Откройте Documents\\Electronic Arts\\The Sims 4\\Mods.\n2. Положите папку DeepRelationships из этого архива в Mods.\n3. В игре включите «Пользовательский контент и моды» и «Моды сценариев».\n4. Удалите localthumbcache.package.\n5. Полностью перезапустите игру и войдите в семью.\n\nКАК ПОНЯТЬ, ЧТО МОД ЗАГРУЗИЛСЯ\nСразу после окончания загрузочного экрана должно появиться уведомление:\n«Глубокие отношения v0.2.0 — Мод успешно загружен. Анализ отношений запущен автоматически.»\n\nДИАГНОСТИКА\nВерсия v0.2.0 специально сделана как один Python-модуль. Она создаёт диагностический файл:\nDocuments\\Electronic Arts\\The Sims 4\\mod_data\\DeepRelationships\\deeprel.log\n\nВ нормальной загрузке в нём будут строки:\nSCRIPT IMPORTED\nGAME IMPORTS OK\nRELATIONSHIP OBSERVERS INSTALLED\nBOOTSTRAP HOOK INSTALLED\nZONE LOADED\nACTIVE SIM FOUND\nHOUSEHOLD FOUND DURING INIT\nNOTIFICATION SHOWN\nRELATIONSHIP ENGINE STARTED\n\nЕсли уведомления нет, пришлите deeprel.log — по нему будет видно точное место остановки.\n\nЧТО ДЕЛАЕТ ЯДРО\n— Отслеживает романтические отношения активной семьи.\n— Для каждого направления отношений хранит Любовь, Доверие, Привязанность, Совместимость и Удовлетворённость.\n— Романтика повышает любовь и удовлетворённость.\n— Положительное дружеское общение укрепляет доверие и привязанность.\n— Негативные изменения сильнее бьют по доверию и удовлетворённости.\n— Долгое отсутствие взаимодействий постепенно снижает удовлетворённость.\n— Высокая привязанность замедляет охлаждение долгих отношений.\n— Определяет состояния пары: «Медовый месяц», «Крепкая пара», «Кризис», «Недоверие», «Отдаление», «Отношения по привычке», «На грани разрыва» и др.\n— Не изменяет стандартные полоски отношений самостоятельно: система наблюдает за обычной игрой и ведёт дополнительные скрытые параметры.\n\nДополнительная диагностическая команда: deeprel.status\nДля обычной игры команды не нужны.\n'''
    path = DIST / 'README_RU.txt'
    path.write_text(text, encoding='utf-8')
    return path


def make_install_zip(ts4script, readme):
    output = DIST / USER_ZIP_NAME
    with zipfile.ZipFile(str(output), 'w', compression=zipfile.ZIP_DEFLATED) as archive:
        archive.write(str(ts4script), arcname='DeepRelationships/' + ts4script.name)
        archive.write(str(readme), arcname='DeepRelationships/README_RU.txt')
    return output


def verify_archives(ts4script, install_zip):
    with zipfile.ZipFile(str(ts4script), 'r') as archive:
        names = archive.namelist()
        if names != ['deep_relationships.pyc']:
            raise RuntimeError('ts4script must contain exactly one module, got: {}'.format(names))
        bad = archive.testzip()
        if bad:
            raise RuntimeError('Corrupt ts4script member: {}'.format(bad))
    with zipfile.ZipFile(str(install_zip), 'r') as archive:
        bad = archive.testzip()
        if bad:
            raise RuntimeError('Corrupt install archive member: {}'.format(bad))


def main():
    clean()
    pyc = compile_script()
    magic = verify_python37(pyc)
    script = make_ts4script(pyc)
    readme = make_readme()
    install_zip = make_install_zip(script, readme)
    verify_archives(script, install_zip)
    print('Python:', os.sys.version)
    print('pyc:', pyc.name, 'magic:', magic)
    print('ts4script members: 1')
    print('ts4script:', script)
    print('install zip:', install_zip)
    print('ts4script size:', script.stat().st_size)
    print('install zip size:', install_zip.stat().st_size)


if __name__ == '__main__':
    main()
