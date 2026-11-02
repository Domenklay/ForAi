# -*- coding: utf-8 -*-
import os
import py_compile
import shutil
import struct
import zipfile
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC = ROOT / 'src'
TUNING = ROOT / 'tuning'
BUILD = ROOT / 'build'
DIST = ROOT / 'dist'

VERSION = '0.4.1'
MOD_BASENAME = 'DeepRelationships_v{}'.format(VERSION)
SCRIPT_NAME = MOD_BASENAME + '.ts4script'
PACKAGE_NAME = MOD_BASENAME + '.package'
USER_ZIP_NAME = MOD_BASENAME + '_INSTALL.zip'

EXPECTED_MAGIC = bytes.fromhex('420d0d0a')
EXPECTED_MODULES = [
    'deep_relationships.pyc',
    'zz_deep_relationships_grievances.pyc',
    'zzy_deep_relationships_moodlets.pyc',
]

T_INTERACTION = 0xE882D22F
T_BUFF = 0x6017E896
T_SIMDATA = 0x545AC67A
T_STBL = 0x220557DA
SIMDATA_GROUP_BUFF = 0x0017E8F6
STBL_GROUP = 0x80000000
COMPRESS_ZLIB = 0x5A42

VIEW_INTERACTION_ID = 16907167177260101633
STBL_BASE_INSTANCE = 0x00DCBB0F7C4E54B1
STBL_ENGLISH_INSTANCE = STBL_BASE_INSTANCE
STBL_RUSSIAN_INSTANCE = (0x12 << 56) | STBL_BASE_INSTANCE

BUFFS = (
    {
        'key': 'light_irritation',
        'name': 'DeepRelationships:Buff_LightIrritation',
        'id': 9809346411725758677,
        'name_key': 0xBB4060E8,
        'desc_key': 0x8ECBAC7D,
        'mood': 14645,
        'weight': 1,
        'icon_path': r'InGame\UI\Icons\Buffs\Buffs_Tense_neg.png',
        'icon_key': '2f7d0004:00000000:c6f6f57c3d2ac7aa',
    },
    {
        'key': 'accumulated_resentment',
        'name': 'DeepRelationships:Buff_AccumulatedResentment',
        'id': 14935880521011841611,
        'name_key': 0xB3695F7A,
        'desc_key': 0xEB42679B,
        'mood': 14632,
        'weight': 1,
        'icon_path': r'InGame\UI\Icons\Buffs\buffs_enemies_neg.png',
        'icon_key': '2f7d0004:00000000:898bcc5a07f0f1d7',
    },
    {
        'key': 'serious_conflict',
        'name': 'DeepRelationships:Buff_SeriousConflict',
        'id': 14816115564650603146,
        'name_key': 0xB491DD97,
        'desc_key': 0xEEF66E18,
        'mood': 14632,
        'weight': 2,
        'icon_path': r'InGame\UI\Icons\Buffs\Buffs_HotHeaded_neg.png',
        'icon_key': '2f7d0004:00000000:78305564a15c24b7',
    },
    {
        'key': 'deep_hurt',
        'name': 'DeepRelationships:Buff_DeepHurt',
        'id': 16750057278039550849,
        'name_key': 0xD1BE4140,
        'desc_key': 0xA091D145,
        'mood': 14643,
        'weight': 2,
        'icon_path': r'InGame\UI\Icons\Buffs\Buff_EmotionSad_neg.png',
        'icon_key': '2f7d0004:00000000:814aef6a4899120b',
    },
    {
        'key': 'betrayed_trust',
        'name': 'DeepRelationships:Buff_BetrayedTrust',
        'id': 14632315915397281344,
        'name_key': 0x92CA45E1,
        'desc_key': 0xE8E44BDE,
        'mood': 14643,
        'weight': 2,
        'icon_path': r'InGame\UI\Icons\Buffs\buffs_woohoo.png',
        'icon_key': '2f7d0004:00000000:d8a30dbc6c591ddd',
    },
)

RU_STRINGS = {
    0xBB4060E8: 'Лёгкое раздражение',
    0x8ECBAC7D: 'Между партнёрами осталось напряжение. Мелкие обиды пока не отпускают.',
    0xB3695F7A: 'Накопившаяся обида',
    0xEB42679B: 'Слишком много неприятных эпизодов осталось без решения. Простые знаки внимания уже не стирают накопившееся недовольство.',
    0xB491DD97: 'Серьёзный конфликт',
    0xEEF66E18: 'Отношения переживают серьёзный конфликт. Доверие и удовлетворённость не восстановятся полностью, пока проблема не решена.',
    0xD1BE4140: 'Глубокая обида',
    0xA091D145: 'Боль от отношений стала слишком сильной. Сим продолжает помнить то, что произошло, даже если любовь ещё осталась.',
    0x92CA45E1: 'Разбитое доверие',
    0xE8E44BDE: 'Измена оставила глубокий след. Восстановить доверие будет намного сложнее, чем просто вернуть романтику.',
}

EN_STRINGS = {
    0xBB4060E8: 'Lingering Irritation',
    0x8ECBAC7D: 'There is still tension between the partners. Small hurts have not quite faded yet.',
    0xB3695F7A: 'Accumulated Resentment',
    0xEB42679B: 'Too many unpleasant moments were left unresolved. Simple affection can no longer erase the built-up resentment.',
    0xB491DD97: 'Serious Relationship Conflict',
    0xEEF66E18: 'This relationship is going through a serious conflict. Trust and satisfaction cannot fully recover until the problem is addressed.',
    0xD1BE4140: 'Deeply Hurt',
    0xA091D145: 'The pain in this relationship has become difficult to ignore. What happened still matters, even if love remains.',
    0x92CA45E1: 'Betrayed Trust',
    0xE8E44BDE: 'Infidelity left a deep mark. Rebuilding trust will be much harder than simply rebuilding romance.',
}


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
            raise RuntimeError(
                'Unexpected pyc magic for {}: {} (expected {})'.format(
                    pyc_path.name, magic.hex(), EXPECTED_MAGIC.hex()
                )
            )
        verified.append((pyc_path.name, magic.hex()))
    return verified


def make_ts4script(pyc_paths):
    output = DIST / SCRIPT_NAME
    with zipfile.ZipFile(str(output), 'w', compression=zipfile.ZIP_DEFLATED) as archive:
        for pyc_path in sorted(pyc_paths, key=lambda path: path.name):
            archive.write(str(pyc_path), arcname=pyc_path.name)
    return output


def fnv1_32_lower(text):
    value = 0x811C9DC5
    for byte in text.lower().encode('utf-8'):
        value = ((value * 0x01000193) & 0xFFFFFFFF) ^ byte
    return value


class _SimDataWriter:
    def __init__(self):
        self.buf = bytearray()
        self.fixups = []
        self.marks = {}

    def mark(self, key):
        self.marks[key] = len(self.buf)

    def u32(self, value):
        self.buf += struct.pack('<I', value & 0xFFFFFFFF)

    def i32(self, value):
        self.buf += struct.pack('<i', value)

    def u16(self, value):
        self.buf += struct.pack('<H', value & 0xFFFF)

    def raw(self, value):
        self.buf += value

    def align(self, alignment=16):
        while len(self.buf) % alignment:
            self.buf += b'\x00'

    def ptr(self, key):
        self.fixups.append((len(self.buf), key))
        self.buf += b'\x00\x00\x00\x00'

    def null(self):
        self.buf += struct.pack('<i', -1)

    def finish(self):
        for pos, key in self.fixups:
            if key not in self.marks:
                raise KeyError('Unresolved SimData pointer {}'.format(key))
            struct.pack_into('<i', self.buf, pos, self.marks[key] - pos)
        return bytes(self.buf)


BUFF_SCHEMA = {
    'row_size': 96,
    'schema_hash': 3706029267,
    'columns': (
        ('audio_sting_on_add', 19, 0, 0),
        ('audio_sting_on_remove', 19, 0, 16),
        ('buff_description', 20, 0, 32),
        ('buff_name', 20, 0, 36),
        ('cas_vfx', 11, 0, 40),
        ('icon', 19, 0, 48),
        ('mood_type', 18, 0, 64),
        ('mood_weight', 6, 0, 72),
        ('plumbob_vfx', 11, 0, 76),
        ('timeout_string', 20, 0, 80),
        ('timeout_string_no_next_buff', 20, 0, 84),
        ('ui_sort_order', 6, 0, 88),
    ),
}


def build_buff_simdata(instance_name):
    row_size = BUFF_SCHEMA['row_size']
    columns = BUFF_SCHEMA['columns']
    writer = _SimDataWriter()
    writer.raw(b'DATA')
    writer.u32(0x101)
    writer.ptr('tables')
    writer.i32(1)
    writer.ptr('schema')
    writer.i32(1)

    writer.mark('tables')
    writer.ptr('s_instance')
    writer.u32(fnv1_32_lower(instance_name))
    writer.ptr('schema')
    writer.u32(0x0D)
    writer.u32(row_size)
    writer.ptr('rows')
    writer.u32(1)

    writer.align(16)
    writer.mark('rows')
    writer.raw(b'\x00' * row_size)

    writer.align(16)
    writer.mark('schema')
    writer.ptr('s_class')
    writer.u32(T_BUFF)
    writer.u32(BUFF_SCHEMA['schema_hash'])
    writer.u32(row_size)
    writer.ptr('columns')
    writer.i32(len(columns))

    writer.mark('columns')
    for name, col_type, flags, offset in columns:
        writer.ptr('s_col_' + name)
        writer.u32(fnv1_32_lower(name))
        writer.u16(col_type)
        writer.u16(flags)
        writer.u32(offset)
        writer.null()

    writer.mark('s_instance')
    writer.raw(instance_name.encode('utf-8') + b'\x00')
    writer.mark('s_class')
    writer.raw(b'Buff\x00')
    for name, _, _, _ in columns:
        writer.mark('s_col_' + name)
        writer.raw(name.encode('utf-8') + b'\x00')
    return writer.finish()


def build_stbl(strings):
    body = bytearray()
    total_string_size = 0
    for key, text in strings.items():
        encoded = str(text).encode('utf-8')
        if len(encoded) > 0xFFFF:
            raise ValueError('STBL string too long for key 0x{:08X}'.format(key))
        body += struct.pack('<IBH', key & 0xFFFFFFFF, 0, len(encoded))
        body += encoded
        total_string_size += len(encoded) + 1
    header = b'STBL' + struct.pack(
        '<HBQHI', 5, 0, len(strings), 0, total_string_size
    )
    return header + bytes(body)


def make_buff_xml(buff):
    return (
        '<?xml version="1.0" encoding="utf-8"?>\n'
        '<I c="Buff" i="buff" m="buffs.buff" n="{name}" s="{id}">\n'
        '  <T n="buff_description">0x{desc_key:08X}</T>\n'
        '  <T n="buff_name">0x{name_key:08X}</T>\n'
        '  <T n="icon" p="{icon_path}">{icon_key}</T>\n'
        '  <T n="mood_type">{mood}</T>\n'
        '  <T n="mood_weight">{weight}</T>\n'
        '  <T n="show_timeout">False</T>\n'
        '  <T n="visible">True</T>\n'
        '</I>\n'
    ).format(**buff).encode('utf-8')


def write_dbpf(path, resources):
    body = bytearray()
    index_rows = []
    offset = 96
    for resource_type, group, instance, data in resources:
        compressed = zlib.compress(data, 9)
        body += compressed
        index_rows.append((
            resource_type, group, instance, offset, len(compressed), len(data)
        ))
        offset += len(compressed)

    index = bytearray(struct.pack('<I', 0))
    for resource_type, group, instance, resource_offset, compressed_size, raw_size in index_rows:
        index += struct.pack(
            '<IIIIIIIHH',
            resource_type,
            group,
            (instance >> 32) & 0xFFFFFFFF,
            instance & 0xFFFFFFFF,
            resource_offset,
            compressed_size | 0x80000000,
            raw_size,
            COMPRESS_ZLIB,
            1,
        )

    header = bytearray(96)
    header[0:4] = b'DBPF'
    struct.pack_into('<I', header, 0x04, 2)
    struct.pack_into('<I', header, 0x08, 1)
    struct.pack_into('<I', header, 0x20, len(index_rows))
    struct.pack_into('<I', header, 0x24, len(index_rows))
    struct.pack_into('<I', header, 0x2C, len(index))
    struct.pack_into('<I', header, 0x3C, 3)
    struct.pack_into('<Q', header, 0x40, 96 + len(body))

    path.write_bytes(bytes(header) + bytes(body) + bytes(index))
    return len(index_rows)


def build_tuning_package():
    resources = []
    interaction = (TUNING / 'deeprel_relationship_view.xml').read_bytes()
    resources.append((T_INTERACTION, 0, VIEW_INTERACTION_ID, interaction))

    for buff in BUFFS:
        resources.append((T_BUFF, 0, buff['id'], make_buff_xml(buff)))
        resources.append((
            T_SIMDATA,
            SIMDATA_GROUP_BUFF,
            buff['id'],
            build_buff_simdata(buff['name'])
        ))

    resources.append((
        T_STBL,
        STBL_GROUP,
        STBL_ENGLISH_INSTANCE,
        build_stbl(EN_STRINGS)
    ))
    resources.append((
        T_STBL,
        STBL_GROUP,
        STBL_RUSSIAN_INSTANCE,
        build_stbl(RU_STRINGS)
    ))

    output = DIST / PACKAGE_NAME
    count = write_dbpf(output, resources)
    if count != 13:
        raise RuntimeError('Expected 13 package resources, got {}'.format(count))
    return output


def read_dbpf_index(path):
    data = path.read_bytes()
    if data[:4] != b'DBPF':
        raise RuntimeError('Package is not DBPF')
    count = struct.unpack_from('<I', data, 0x24)[0]
    index_size = struct.unpack_from('<I', data, 0x2C)[0]
    index_offset = struct.unpack_from('<Q', data, 0x40)[0]
    if index_offset <= 0 or index_offset + index_size > len(data):
        raise RuntimeError('Invalid DBPF index bounds')
    index = data[index_offset:index_offset + index_size]
    flags = struct.unpack_from('<I', index, 0)[0]
    if flags != 0:
        raise RuntimeError('Unexpected DBPF index flags {}'.format(flags))
    pos = 4
    rows = []
    for _ in range(count):
        resource_type, group, hi, lo, offset, file_size, mem_size, compression, committed = struct.unpack_from(
            '<IIIIIIIHH', index, pos
        )
        pos += 32
        rows.append((
            resource_type, group, (hi << 32) | lo, offset,
            file_size, mem_size, compression, committed
        ))
    if pos != len(index):
        raise RuntimeError('Unexpected DBPF index length')
    return data, rows


def verify_package(package):
    data, rows = read_dbpf_index(package)
    if len(rows) != 13:
        raise RuntimeError('Expected 13 tuning resources, got {}'.format(len(rows)))

    counts = {}
    for row in rows:
        counts[row[0]] = counts.get(row[0], 0) + 1
    expected_counts = {
        T_INTERACTION: 1,
        T_BUFF: 5,
        T_SIMDATA: 5,
        T_STBL: 2,
    }
    if counts != expected_counts:
        raise RuntimeError('Unexpected resource type counts: {}'.format(counts))

    expected_buff_ids = set(buff['id'] for buff in BUFFS)
    actual_buff_ids = set(row[2] for row in rows if row[0] == T_BUFF)
    if actual_buff_ids != expected_buff_ids:
        raise RuntimeError('Buff IDs mismatch')

    stbl_ids = set(row[2] for row in rows if row[0] == T_STBL)
    if stbl_ids != {STBL_ENGLISH_INSTANCE, STBL_RUSSIAN_INSTANCE}:
        raise RuntimeError('STBL locale instances mismatch')

    for resource_type, group, instance, offset, file_size, mem_size, compression, _ in rows:
        compressed_size = file_size & 0x7FFFFFFF
        raw = data[offset:offset + compressed_size]
        if file_size & 0x80000000:
            if compression != COMPRESS_ZLIB:
                raise RuntimeError('Unexpected compression for 0x{:016X}'.format(instance))
            raw = zlib.decompress(raw)
        if len(raw) != mem_size:
            raise RuntimeError('Resource size mismatch for 0x{:016X}'.format(instance))
        if resource_type == T_STBL and raw[:4] != b'STBL':
            raise RuntimeError('Invalid STBL resource')
        if resource_type == T_SIMDATA and raw[:4] != b'DATA':
            raise RuntimeError('Invalid Buff SimData resource')
    return counts


def make_readme():
    text = '''ГЛУБОКИЕ ОТНОШЕНИЯ — v0.4.1

Совместимость: The Sims 4 PC 1.127.x, DX11.
Сторонние библиотеки не нужны.

ВАЖНО ПРИ ОБНОВЛЕНИИ
Удалите старую папку DeepRelationships целиком. Данные отношений в mod_data удалять НЕ нужно — они сохранятся.

УСТАНОВКА
1. Откройте Documents\\Electronic Arts\\The Sims 4\\Mods.
2. Положите папку DeepRelationships из этого архива в Mods.
3. В папке должны лежать ДВА файла:
   DeepRelationships_v0.4.1.ts4script
   DeepRelationships_v0.4.1.package
4. В игре должны быть включены «Пользовательский контент и моды» и «Моды сценариев».
5. Удалите localthumbcache.package.
6. Полностью перезапустите игру и войдите в семью.

НОВОЕ В v0.4.1 — НАСТОЯЩИЕ МУДЛЕТЫ
Мудлеты отображаются в обычной панели настроения Sims 4 и реально влияют на эмоцию сима.

• Лёгкое раздражение — НАПРЯЖЕНИЕ +1.
  Появляется при общем уровне обиды 8–24.

• Накопившаяся обида — ЗЛОСТЬ +1.
  Появляется при общем уровне обиды 25–44.

• Серьёзный конфликт — ЗЛОСТЬ +2.
  Появляется при общем уровне обиды 45–69.

• Глубокая обида — ГРУСТЬ +2.
  Появляется при общем уровне обиды 70+.

• Разбитое доверие — ГРУСТЬ +2.
  Отдельный мудлет после измены. Он может существовать одновременно с обычным мудлетом конфликта.

КАК ОНИ РАБОТАЮТ
— Мудлет получает именно тот сим, который хранит обиду на партнёра.
— При усилении конфликта более слабый мудлет автоматически заменяется сильным.
— Когда обиды постепенно ослабевают, мудлет тоже ослабевает или исчезает.
— Если у сима несколько романтических отношений, общий конфликтный мудлет берётся по самой тяжёлой активной обиде.
— Мудлет измены остаётся, пока соответствующая обида «Измена» не угаснет.
— Система синхронизируется при загрузке семьи, появлении новой обиды и каждые 6 игровых часов.

ЛОКАЛИЗАЦИЯ
В пакет включены русские и английские строки. На русской игре названия и описания мудлетов должны быть на русском.

ОСТАЛЬНАЯ СИСТЕМА
Сохраняются все функции v0.4.0: Любовь, Доверие, Привязанность, Совместимость, Удовлетворённость, состояния пары, «Наши отношения», накопленные обиды, недостаток внимания и определение измены по ванильному relationship bit.

ДАННЫЕ
Существующий файл отношений сохраняется:
Documents\\Electronic Arts\\The Sims 4\\mod_data\\DeepRelationships\\deep_relationships_state.json

ДИАГНОСТИКА
Лог:
Documents\\Electronic Arts\\The Sims 4\\mod_data\\DeepRelationships\\deeprel.log

При нормальной загрузке должны появиться строки:
MOODLET SYSTEM INSTALLED v0.4.1
MOODLET SYSTEM ACTIVE: all 5 buffs loaded

Команды для обычной игры не нужны.
'''
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


def verify_archives(ts4script, package, install_zip):
    with zipfile.ZipFile(str(ts4script), 'r') as archive:
        names = sorted(archive.namelist())
        if names != EXPECTED_MODULES:
            raise RuntimeError('Unexpected ts4script modules: {}'.format(names))
        bad = archive.testzip()
        if bad:
            raise RuntimeError('Corrupt ts4script member: {}'.format(bad))

    counts = verify_package(package)

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
            raise RuntimeError(
                'Unexpected install archive contents: {}'.format(sorted(names))
            )
    return counts


def main():
    clean()
    pycs = compile_scripts()
    verified = verify_python37(pycs)
    script = make_ts4script(pycs)
    package = build_tuning_package()
    readme = make_readme()
    install_zip = make_install_zip(script, package, readme)
    counts = verify_archives(script, package, install_zip)

    print('Python:', os.sys.version)
    for name, magic in verified:
        print('pyc:', name, 'magic:', magic)
    print('ts4script members:', len(pycs))
    print('package resources:', sum(counts.values()))
    print('package resource types:', counts)
    print('moodlet buffs:', len(BUFFS))
    print('locales: English + Russian')
    print('ts4script:', script)
    print('package:', package)
    print('install zip:', install_zip)
    print('ts4script size:', script.stat().st_size)
    print('package size:', package.stat().st_size)
    print('install zip size:', install_zip.stat().st_size)


if __name__ == '__main__':
    main()
