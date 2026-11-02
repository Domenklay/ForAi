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
VERSION = '0.1.1'
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
        for pyc_path in sorted(pyc_paths, key=lambda p: p.name):
            archive.write(str(pyc_path), arcname=pyc_path.name)
    return output


def make_readme():
    text = '''ГЛУБОКИЕ ОТНОШЕНИЯ — v0.1.1\n\nСовместимость: The Sims 4 PC 1.127.x, DX11.\nЭто отдельный мод; прошлые семейные моды ему не нужны.\n\nВАЖНО ПРИ ОБНОВЛЕНИИ\nУдалите старый DeepRelationships_v0.1.0.ts4script перед установкой этой версии. Одновременно должна лежать только одна версия.\n\nУСТАНОВКА\n1. Откройте Documents\\Electronic Arts\\The Sims 4\\Mods.\n2. Положите папку DeepRelationships из этого архива в Mods.\n3. В игре должны быть включены «Пользовательский контент и моды» и «Моды сценариев».\n4. Полностью перезапустите игру.\n\nКАК ПОНЯТЬ, ЧТО МОД ЗАГРУЗИЛСЯ\nПосле входа в семью и завершения загрузочного экрана должно появиться уведомление «Глубокие отношения v0.1.1». В v0.1.1 запуск переведён на прямой хук окончания загрузочного экрана — тот же тип запуска, который использовался в рабочем семейном модуле.\n\nЧТО ДЕЛАЕТ МОД\n— Отслеживает романтические отношения активной семьи.\n— Для каждого направления хранит: Любовь, Доверие, Привязанность, Совместимость, Удовлетворённость.\n— Романтика повышает любовь и удовлетворённость.\n— Положительное дружеское общение укрепляет доверие и привязанность.\n— Негативные изменения сильнее бьют по доверию и удовлетворённости.\n— Долгое отсутствие общения постепенно снижает удовлетворённость; высокая привязанность замедляет спад.\n— Определяет состояния: «Медовый месяц», «Крепкая пара», «Кризис», «Недоверие», «Отдаление», «Отношения по привычке», «На грани разрыва» и др.\n— Данные сохраняются отдельно для сохранений в Documents\\Electronic Arts\\The Sims 4\\mod_data\\DeepRelationships.\n\nДИАГНОСТИКА\nКоманда deeprel.report показывает точные числа активного сима, но для обычной работы мода не нужна.\n'''
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
