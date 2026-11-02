const fs = require('fs');
const path = require('path');
const { SimDataResource } = require('@s4tk/models');

const root = path.resolve(__dirname, '..');
const outDir = path.join(root, 'build_v064_simdata');
fs.mkdirSync(outDir, { recursive: true });

const buffs = [
  ['nervous','LWC:buff_nervous','EAEF833E','A89B7FA4',14645,2,'C6F6F57C3D2AC7AA'],
  ['betrayal','LWC:buff_betrayal','483CF4C7','A9CA817B',14643,3,'D8A30DBC6C591DDD'],
  ['after_fight','LWC:buff_after_fight','D4D7E812','173916D5',14632,2,'898BCC5A07F0F1D7'],
  ['broken_heart','LWC:buff_broken_heart','50FE7FE4','9243D6A3',14643,3,'D8A30DBC6C591DDD'],
  ['pride','LWC:buff_pride','3D1D92B5','69F1BF3E',14634,2,'AFDF63731E01A494'],
  ['relief','LWC:buff_relief','D1665924','C00FEC59',14640,2,'AFDF63731E01A494'],
  ['burnout','LWC:buff_burnout','BBDC7872','6E0D7D7C',14645,3,'C6F6F57C3D2AC7AA'],
  ['guilt','LWC:buff_guilt','A71D19D6','295EADD5',14635,2,'898BCC5A07F0F1D7'],
  ['grief','LWC:buff_grief','C6FDFC30','28F1653E',14643,3,'D8A30DBC6C591DDD'],
];

function makeXml(name, nameKey, descKey, mood, weight, iconInst) {
  return `<?xml version="1.0" encoding="utf-8"?>
<SimData version="0x00000101" u="0x00000000">
  <Instances>
    <I name="${name}" schema="Buff" type="Object">
      <T name="audio_sting_on_add">FD04E3BE-001407EC-8AF8B916CF64C646</T>
      <T name="audio_sting_on_remove">FD04E3BE-001407EC-3BF33216A25546EA</T>
      <T name="buff_description">0x${descKey}</T>
      <T name="buff_name">0x${nameKey}</T>
      <T name="cas_vfx"></T>
      <T name="icon">00B2D882-00000000-${iconInst}</T>
      <T name="mood_type">${mood}</T>
      <T name="mood_weight">${weight}</T>
      <T name="plumbob_vfx"></T>
      <T name="timeout_string">0x00000000</T>
      <T name="timeout_string_no_next_buff">0x00000000</T>
      <T name="ui_sort_order">1</T>
    </I>
  </Instances>
  <Schemas>
    <Schema name="Buff" schema_hash="0xDCE584D3">
      <Columns>
        <Column name="audio_sting_on_add" type="ResourceKey" flags="0x00000000" />
        <Column name="audio_sting_on_remove" type="ResourceKey" flags="0x00000000" />
        <Column name="buff_description" type="LocalizationKey" flags="0x00000000" />
        <Column name="buff_name" type="LocalizationKey" flags="0x00000000" />
        <Column name="cas_vfx" type="String" flags="0x00000000" />
        <Column name="icon" type="ResourceKey" flags="0x00000000" />
        <Column name="mood_type" type="TableSetReference" flags="0x00000000" />
        <Column name="mood_weight" type="Int32" flags="0x00000000" />
        <Column name="plumbob_vfx" type="String" flags="0x00000000" />
        <Column name="timeout_string" type="LocalizationKey" flags="0x00000000" />
        <Column name="timeout_string_no_next_buff" type="LocalizationKey" flags="0x00000000" />
        <Column name="ui_sort_order" type="Int32" flags="0x00000000" />
      </Columns>
    </Schema>
  </Schemas>
</SimData>`;
}

for (const [file, name, nameKey, descKey, mood, weight, icon] of buffs) {
  const xml = makeXml(name, nameKey, descKey, mood, weight, icon);
  const model = SimDataResource.fromXml(xml);
  const buffer = model.getBuffer();
  if (buffer.slice(0,4).toString('ascii') !== 'DATA') throw new Error(`Bad SimData for ${file}`);
  fs.writeFileSync(path.join(outDir, `${file}.simdata`), buffer);
  console.log(file, buffer.length);
}
if (buffs.length !== 9) throw new Error('Expected 9 moodlet SimData resources');
console.log('SimData generated:', buffs.length);
