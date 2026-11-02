# -*- coding: utf-8 -*-
import os
import py_compile
import shutil
import struct
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC = ROOT / 'src'
TUNING = ROOT / 'tuning'
BUILD = ROOT / 'build'
DIST = ROOT / 'dist'
VERSION = '0.3.0'
MOD_BASENAME = 'DeepRelationships_v{}'.format(VERSION)
SCRIPT_NAME = MOD_BASENAME + '.ts4script'
PACKAGE_NAME = MOD_BASENAME + '.package'
USER_ZIP_NAME = MOD_BASENAME + '_INSTALL.zip'
EXPECTED_MAGIC = bytes.fromhex('420d0d0a')
INTERACTION_TUNING_TYPE = 0xE882D22F
VIEW_INTERACTION_ID = 16907167177260101633


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


def build_tuning_package():
    source = TUNING / 'deeprel_relationship_view.xml'
    resource = source.read_bytes()
    resource_offset = 96
    index_offset = resource_offset + len(resource)
    index = struct.pack(
        '<IIIIIIII',
        INTERACTION_TUNING_TYPE,
        0,
        VIEW_INTERACTION_ID >> 32,
        VIEW_INTERACTION_ID & 0xFFFFFFFF,
        resource_offset,
        len(resource) | 0x80000000,
        len(resource),
        0x00010000,
    )
    header = bytearray(96)
    struct.pack_into('<4sII', header, 0, b'DBPF', 2, 1)
    struct.pack_into('<III', header, 36, 1, index_offset, 4 + len(index))
    struct.pack_into('<IQ', header, 60, 3, index_offset)
    output = DIST / PACKAGE_NAME
    output.write_bytes(header + resource + struct.pack('<I', 0) + index)
    return output


def make_readme():
    text = '''ГЛУБОКИЕ ОТНОШЕНИЯ — v0.3.0\n\nСовместимость: The Sims 4 PC 1.127.x, DX11.\nСторонние библиотеки не нужны.\n\nВАЖНО ПРИ ОБНОВЛЕНИИ\nУдалите старую папку DeepRelationships целиком. В Mods одновременно должна оставаться только версия v0.3.0.\n\nУСТАНОВКА\n1. Откройте Documents\\Electronic Arts\\The Sims 4\\Mods.\n2. Положите папку DeepRelationships из этого архива в Mods.\n3. В папке должны лежать ДВА файла:\n   DeepRelationships_v0.3.0.ts4script\n   DeepRelationships_v0.3.0.package\n4. В игре включите «Пользовательский контент и моды» и «Моды сценариев».\n5. Удалите localthumbcache.package.\n6. Полностью перезапустите игру и войдите в семью.\n\nЧТО НОВОГО В v0.3\n— При нажатии на романтического партнёра появляется действие «Наши отношения».\n— Открывается отдельное окно со значениями в ОБЕ стороны: один партнёр может любить, доверять и быть доволен сильнее другого.\n— Показаны: Любовь, Доверие, Привязанность, Совместимость, Удовлетворённость и текущее состояние пары.\n— Для тестирования рядом с оценкой показывается точное число 0–100.\n\nПРИМЕР\nАлиса → Максим\nСостояние: Крепкая пара\nЛюбовь: очень высокая (88)\nДоверие: средняя (58)\n...\n\nМаксим → Алиса\nСостояние: Кризис\nЛюбовь: высокая (73)\nДоверие: низкая (31)\n...\n\nДИАГНОСТИКА\nЛог остаётся здесь:\nDocuments\\Electronic Arts\\The Sims 4\\mod_data\\DeepRelationships\\deeprel.log\n\nПри нормальной загрузке должны появиться строки:\nSCRIPT IMPORTED\nGAME IMPORTS OK\nUI SIM.ON_ADD HOOK INSTALLED\nRELATIONSHIP OBSERVERS INSTALLED\nBOOTSTRAP HOOK INSTALLED\nZONE LOADED\nUI AFFORDANCE ADDED TO SIM\nRELATIONSHIP ENGINE STARTED\n\nЕсли .ts4script загрузился, но .package отсутствует или не читается, игра отдельно сообщит об этом уведомлением.\n\nОбычные команды не нужны. Дополнительная проверка: deeprel.status\n'''
    path = DIST / 'README_RU.txt'
    path.write_text(text, encoding='utf-8')
    return path


def make_install_zip(ts4script, package, readme):
    output = DIST / USER_ZIP_NAME
    with zipfile.ZipFile(str(output), 'w', compression=zipfile.ZIP_DEFLATED) as archive:
        archive.write(str(ts4script), arcname='DeepRelationships/' + ts4script.name)
        archive.write(str(package), arcname='DeepRelationships/' + package.name)
        archive.write(str(readme), arcname='DeepRelationships/README_RU.txt')
    return output


def verify_package(package):
    data = package.read_bytes()
    if data[:4] != b'DBPF':
        raise RuntimeError('Package is not DBPF')
    if len(data) < 132:
        raise RuntimeError('Package unexpectedly small')
    resource_count, index_offset, index_size = struct.unpack_from('<III', data, 36)
    if resource_count != 1:
        raise RuntimeError('Expected 1 tuning resource, got {}'.format(resource_count))
    if index_size != 36:
        raise RuntimeError('Unexpected package index size {}'.format(index_size))
    if index_offset >= len(data):
        raise RuntimeError('Invalid package index offset')


def verify_archives(ts4script, package, install_zip):
    with zipfile.ZipFile(str(ts4script), 'r') as archive:
        names = archive.namelist()
        if names != ['deep_relationships.pyc']:
            raise RuntimeError('ts4script must contain exactly one module, got: {}'.format(names))
        bad = archive.testzip()
        if bad:
            raise RuntimeError('Corrupt ts4script member: {}'.format(bad))
    verify_package(package)
    with zipfile.ZipFile(str(install_zip), 'r') as archive:
        bad = archive.testzip()
        if bad:
            raise RuntimeError('Corrupt install archive member: {}'.format(bad))
        names = set(archive.namelist())
        expected = {
            'DeepRelationships/' + SCRIPT_NAME,
            'DeepRelationships/' + PACKAGE_NAME,
            'DeepRelationships/README_RU.txt',
        }
        if names != expected:
            raise RuntimeError('Unexpected install archive contents: {}'.format(sorted(names)))


def main():
    clean()
    pyc = compile_script()
    magic = verify_python37(pyc)
    script = make_ts4script(pyc)
    package = build_tuning_package()
    readme = make_readme()
    install_zip = make_install_zip(script, package, readme)
    verify_archives(script, package, install_zip)
    print('Python:', os.sys.version)
    print('pyc:', pyc.name, 'magic:', magic)
    print('ts4script members: 1')
    print('package resources: 1')
    print('ts4script:', script)
    print('package:', package)
    print('install zip:', install_zip)
    print('ts4script size:', script.stat().st_size)
    print('package size:', package.stat().st_size)
    print('install zip size:', install_zip.stat().st_size)


if __name__ == '__main__':
    main()
