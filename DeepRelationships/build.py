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
VERSION = '0.4.0'
MOD_BASENAME = 'DeepRelationships_v{}'.format(VERSION)
SCRIPT_NAME = MOD_BASENAME + '.ts4script'
PACKAGE_NAME = MOD_BASENAME + '.package'
USER_ZIP_NAME = MOD_BASENAME + '_INSTALL.zip'
EXPECTED_MAGIC = bytes.fromhex('420d0d0a')
INTERACTION_TUNING_TYPE = 0xE882D22F
VIEW_INTERACTION_ID = 16907167177260101633
EXPECTED_MODULES = [
    'deep_relationships.pyc',
    'zz_deep_relationships_grievances.pyc',
]


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
        if source.name.startswith('zzz_') or source.name == 'zz_deep_relationships_service.py':
            continue
        target = compiled / (source.stem + '.pyc')
        py_compile.compile(str(source), cfile=str(target), doraise=True)
        outputs.append(target)
    names = sorted(path.name for path in outputs)
    if names != EXPECTED_MODULES:
        raise RuntimeError('Unexpected compiled modules: {}'.format(names))
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
    text = '''ГЛУБОКИЕ ОТНОШЕНИЯ — v0.4.0\n\nСовместимость: The Sims 4 PC 1.127.x, DX11.\nСторонние библиотеки не нужны.\n\nВАЖНО ПРИ ОБНОВЛЕНИИ\nУдалите старую папку DeepRelationships целиком. В Mods одновременно должна оставаться только версия v0.4.0.\n\nУСТАНОВКА\n1. Откройте Documents\\Electronic Arts\\The Sims 4\\Mods.\n2. Положите папку DeepRelationships из этого архива в Mods.\n3. В папке должны лежать ДВА файла:\n   DeepRelationships_v0.4.0.ts4script\n   DeepRelationships_v0.4.0.package\n4. В игре включите «Пользовательский контент и моды» и «Моды сценариев».\n5. Удалите localthumbcache.package.\n6. Полностью перезапустите игру и войдите в семью.\n\nЧТО НОВОГО В v0.4\n— Появилась система накопленных обид.\n— Негативная дружба создаёт обиду «Ссоры и грубость».\n— Негативная романтика создаёт «Романтическую обиду».\n— Если партнёры долго не взаимодействуют, появляется «Недостаток внимания».\n— Ванильный факт измены ROMANTIC_CHEATED_WITH создаёт тяжёлую обиду «Измена».\n— Одинаковые проблемы накапливаются: хранится сила обиды и число эпизодов.\n— Обиды постепенно ослабевают со временем, но тяжёлые исчезают намного медленнее.\n— Серьёзная обида ограничивает максимум Доверия и Удовлетворённости. Одними поцелуями отношения уже нельзя мгновенно вернуть в идеальное состояние.\n— Появились состояния конфликта: «Спокойно», «Лёгкое раздражение», «Накопленная обида», «Серьёзный конфликт», «Глубокая обида».\n\nПРОСМОТР\nНажмите на романтического партнёра → «Наши отношения».\nВнизу каждого направления теперь показаны:\nКонфликт: Накопленная обида (32/100)\nЧто мешает отношениям:\n• Ссоры и грубость — заметная (18) • эпизодов: 3\n• Недостаток внимания — лёгкая (9)\n• Измена — сильная (30)\n\nВАЖНО ПРО ИЗМЕНУ\nМод не пытается угадывать измену по названию анимации. Он слушает стандартный relationship bit игры ROMANTIC_CHEATED_WITH (ID 37265). Поэтому событие создаётся только когда сама игра отмечает связь как измену.\n\nДАННЫЕ\nСтарые данные v0.3 мигрируют автоматически. Новые поля добавляются в тот же файл:\nDocuments\\Electronic Arts\\The Sims 4\\mod_data\\DeepRelationships\\deep_relationships_state.json\n\nДИАГНОСТИКА\nЛог:\nDocuments\\Electronic Arts\\The Sims 4\\mod_data\\DeepRelationships\\deeprel.log\n\nПри нормальной загрузке дополнительно появится строка:\nGRIEVANCE SYSTEM INSTALLED v0.4.0\nGRIEVANCE SYSTEM ACTIVE\n\nОбычные команды не нужны. Дополнительная проверка: deeprel.status\n'''
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
        names = sorted(archive.namelist())
        if names != EXPECTED_MODULES:
            raise RuntimeError('Unexpected ts4script modules: {}'.format(names))
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
    pycs = compile_scripts()
    verified = verify_python37(pycs)
    script = make_ts4script(pycs)
    package = build_tuning_package()
    readme = make_readme()
    install_zip = make_install_zip(script, package, readme)
    verify_archives(script, package, install_zip)
    print('Python:', os.sys.version)
    for name, magic in verified:
        print('pyc:', name, 'magic:', magic)
    print('ts4script members:', len(pycs))
    print('package resources: 1')
    print('ts4script:', script)
    print('package:', package)
    print('install zip:', install_zip)
    print('ts4script size:', script.stat().st_size)
    print('package size:', package.stat().st_size)
    print('install zip size:', install_zip.stat().st_size)


if __name__ == '__main__':
    main()
