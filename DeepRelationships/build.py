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
VERSION = '0.1.0'
MOD_BASENAME = 'DeepRelationships_v{}'.format(VERSION)
SCRIPT_NAME = MOD_BASENAME + '.ts4script'
USER_ZIP_NAME = MOD_BASENAME + '_INSTALL.zip'
EXPECTED_MAGIC = bytes.fromhex('420d0d0a')


def clean():
    for path in (BUILD, DIST):
        if path.exists():
            shutil.rmtree(str(path))
        path.mkdir(parents=True, exist_ok=True)


def compile_scripts():
    compiled = BUILD / 'compiled'
    compiled.mkdir(parents=True, exist_ok=True)
    outputs = []
    for source in sorted(SRC.glob('*.py')):
        target = compiled / (source.stem + '.pyc')
        py_compile.compile(str(source), cfile=str(target), doraise=True)
        outputs.append(target)
    if not outputs:
        raise RuntimeError('No Python sources found')
    return outputs


def verify_python37(pyc_paths):
    verified = []
    for pyc_path in pyc_paths:
        data = pyc_path.read_bytes()
        magic = data[:4]
        if magic != EXPECTED_MAGIC:
            raise RuntimeError('Unexpected pyc magic for {}: {} (expected {})'.format(
                pyc_path.name, magic.hex(), EXPECTED_MAGIC.hex()))
        verified.append((pyc_path.name, magic.hex()))
    return verified


def make_ts4script(pyc_paths):
    output = DIST / SCRIPT_NAME
    with zipfile.ZipFile(str(output), 'w', compression=zipfile.ZIP_DEFLATED) as archive:
        # Alphabetical order is intentional: deep_relationships loads first,
        # zz_deep_relationships_service then moves observation to RelationshipService.
        for pyc_path in sorted(pyc_paths, key=lambda p: p.name):
            archive.write(str(pyc_path), arcname=pyc_path.name)
    return output


def make_readme():
    text = '''ГЛУБОКИЕ ОТНОШЕНИЯ — v0.1.0\n\nСовместимость: The Sims 4 PC 1.127.x, DX11.\nЭто полностью отдельный мод; прошлый мод событий ему не нужен.\n\nУСТАНОВКА\n1. Откройте Documents\\Electronic Arts\\The Sims 4\\Mods.\n2. Создайте папку DeepRelationships (или используйте папку из архива).\n3. Положите в неё DeepRelationships_v0.1.0.ts4script.\n4. В игре включите «Пользовательский контент и моды» и «Моды сценариев».\n5. Перезапустите игру.\n\nКАК ПОНЯТЬ, ЧТО МОД РАБОТАЕТ\nПри первом входе в семью за игровую сессию появится уведомление «Глубокие отношения v0.1.0». Никаких команд для обычной работы не требуется.\n\nЧТО ДЕЛАЕТ v0.1\n— Автоматически отслеживает романтические отношения активной семьи.\n— Для каждого направления отношений хранит: Любовь, Доверие, Привязанность, Совместимость, Удовлетворённость.\n— Показатели одного партнёра могут отличаться от показателей другого.\n— Романтические действия увеличивают любовь и удовлетворённость.\n— Дружеские положительные действия укрепляют доверие и привязанность.\n— Ссоры и отрицательные изменения сильнее бьют по доверию и удовлетворённости.\n— Долгое отсутствие взаимодействий постепенно снижает удовлетворённость; высокая привязанность замедляет этот спад.\n— Система присваивает состояниям пары названия: «Медовый месяц», «Крепкая пара», «Сильная привязанность», «Кризис», «Недоверие», «Отдаление», «Отношения по привычке», «На грани разрыва» и др.\n— При смене важного состояния появляется уведомление.\n— Данные сохраняются отдельно для каждого сохранения в Documents\\Electronic Arts\\The Sims 4\\mod_data\\DeepRelationships.\n\nДИАГНОСТИКА\nКоманда deeprel.report существует только для проверки и показывает точные числа активного сима. Для обычной игры она не нужна.\n\nПРИМЕЧАНИЕ\nЭто ядро v0.1. Следующая логичная версия — накопленные обиды, причины конфликтов и полноценное примирение.\n'''
    path = DIST / 'README_RU.txt'
    path.write_text(text, encoding='utf-8')
    return path


def make_install_zip(ts4script, readme):
    output = DIST / USER_ZIP_NAME
    with zipfile.ZipFile(str(output), 'w', compression=zipfile.ZIP_DEFLATED) as archive:
        archive.write(str(ts4script), arcname='DeepRelationships/' + ts4script.name)
        archive.write(str(readme), arcname='DeepRelationships/README_RU.txt')
    return output


def main():
    clean()
    pycs = compile_scripts()
    verified = verify_python37(pycs)
    script = make_ts4script(pycs)
    readme = make_readme()
    install_zip = make_install_zip(script, readme)
    print('Python:', os.sys.version)
    for name, magic in verified:
        print('pyc:', name, 'magic:', magic)
    print('ts4script:', script)
    print('install zip:', install_zip)
    print('ts4script size:', script.stat().st_size)
    print('install zip size:', install_zip.stat().st_size)


if __name__ == '__main__':
    main()
