using System.Text;
using LlamaLogic.Packages;
using LlamaLogic.Packages.Models;

const ulong interactionId = 8939761482420579312UL;
const ulong stblBase = 0x00A5DD2A333D6FADUL;
byte[] locales = { 0x00,0x01,0x02,0x03,0x04,0x05,0x06,0x07,0x08,0x0B,0x0C,0x0D,0x0E,0x0F,0x11,0x12,0x13,0x15 };

var buffs = new (string File, ulong Id, uint NameKey, uint DescKey, string Name, string Desc, int Mood, int Weight, int Duration, string Icon)[]
{
    ("nervous",2241663046608037664UL,0xEAEF833E,0xA89B7FA4,"На нервах","Последние события не дают расслабиться. Мысли постоянно возвращаются к проблемам.",14645,2,240,"2f7d0004:00000000:c6f6f57c3d2ac7aa"),
    ("betrayal",5174297497776617278UL,0x483CF4C7,0xA9CA817B,"Предательство","Доверие разрушено. Осознание чужой неверности всё ещё причиняет боль.",14643,3,720,"2f7d0004:00000000:d8a30dbc6c591ddd"),
    ("after_fight",8139445382139128986UL,0xD4D7E812,0x173916D5,"После драки","Адреналин ещё не ушёл. Конфликт оставил после себя злость.",14632,2,240,"2f7d0004:00000000:898bcc5a07f0f1d7"),
    ("broken_heart",8759880793873706267UL,0x50FE7FE4,0x9243D6A3,"Разбитое сердце","Отношения закончились, а чувства ещё нет. Нужно время, чтобы пережить это.",14643,3,1440,"2f7d0004:00000000:d8a30dbc6c591ddd"),
    ("pride",5272924670220022269UL,0x3D1D92B5,0x69F1BF3E,"Гордость за себя","Труд и риск окупились. Есть повод почувствовать уверенность в себе.",14634,2,480,"2f7d0004:00000000:afdf63731e01a494"),
    ("relief",3878443874848191958UL,0xD1665924,0xC00FEC59,"Облегчение","Тяжёлый момент позади. Наконец можно немного выдохнуть.",14640,2,360,"2f7d0004:00000000:afdf63731e01a494"),
    ("burnout",6572247178655976097UL,0xBBDC7872,0x6E0D7D7C,"Выгорание","Слишком долго на пределе. Даже обычные дела теперь требуют лишних сил.",14645,3,720,"2f7d0004:00000000:c6f6f57c3d2ac7aa"),
    ("guilt",3178156748154324375UL,0xA71D19D6,0x295EADD5,"Чувство вины","Решение было выгодным, но неприятное чувство после него никуда не делось.",14635,2,480,"2f7d0004:00000000:898bcc5a07f0f1d7")
};

string profileXml = """<?xml version="1.0" encoding="utf-8"?>
<I c="LWCProfileInteraction" i="interaction" m="life_with_consequences" n="LWC:Profile" s="8939761482420579312">
  <V n="_saveable" t="disabled" />
  <T n="category">0</T>
  <V n="content_score" t="disabled" />
  <T n="display_name">0x08E2BF35</T>
  <V n="pie_menu_icon" t="enabled"><V n="enabled" t="resource_key"><U n="resource_key"><T n="key">2f7d0004:00000000:25eea5cdba6a6fd6</T></U></V></V>
  <U n="progress_bar_enabled"><T n="bar_enabled">False</T></U>
  <E n="target_type">OBJECT</E>
</I>""";

string BuffXml((string File, ulong Id, uint NameKey, uint DescKey, string Name, string Desc, int Mood, int Weight, int Duration, string Icon) b)
{
    return $"""<?xml version="1.0" encoding="utf-8"?>
<I c="Buff" i="buff" m="buffs.buff" n="LWC:buff_{b.File}" s="{b.Id}">
  <V n="_temporary_commodity_info" t="enabled"><U n="enabled"><T n="max_duration">{b.Duration}</T></U></V>
  <T p="InGame\Audio\Stings\sting_buff_gain.propx" n="audio_sting_on_add">39b2aa4a:00000000:8af8b916cf64c646</T>
  <T p="InGame\Audio\Stings\sting_buff_loss.propx" n="audio_sting_on_remove">39b2aa4a:00000000:3bf33216a25546ea</T>
  <T n="buff_description">0x{b.DescKey:X8}</T>
  <T n="buff_name">0x{b.NameKey:X8}</T>
  <T n="icon">{b.Icon}</T>
  <T n="mood_type">{b.Mood}</T>
  <T n="mood_weight">{b.Weight}</T>
  <T n="refresh_on_add">True</T>
  <T n="show_timeout">True</T>
  <T n="visible">True</T>
</I>""";
}

var stbl = new StringTableModel();
stbl.Set(0x08E2BF35, "Life With Consequences");
foreach (var b in buffs)
{
    stbl.Set(b.NameKey, b.Name);
    stbl.Set(b.DescKey, b.Desc);
}
var stblBytes = stbl.Encode().ToArray();

var root = Directory.GetCurrentDirectory();
var dist = Path.Combine(root, "dist_v061");
Directory.CreateDirectory(dist);
var outputPath = Path.Combine(dist, "LifeWithConsequences_0.6.1.package");

using (var package = new DataBasePackedFile { CreationTime = DateTimeOffset.UnixEpoch, UpdatedTime = DateTimeOffset.UnixEpoch })
{
    package.Set(new ResourceKey((ResourceType)0xE882D22F, 0x00000000, interactionId), Encoding.UTF8.GetBytes(profileXml), CompressionMode.ForceOff);
    foreach (var b in buffs)
    {
        package.Set(new ResourceKey((ResourceType)0x6017E896, 0x00000000, b.Id), Encoding.UTF8.GetBytes(BuffXml(b)), CompressionMode.ForceOff);
    }
    foreach (var locale in locales)
    {
        var instance = ((ulong)locale << 56) | stblBase;
        package.Set(new ResourceKey(ResourceType.StringTable, 0x80000000, instance), stblBytes, CompressionMode.ForceOff);
    }
    package.SaveAs(outputPath, ResourceKeyOrder.TypeGroupInstance);
}

using (var check = new DataBasePackedFile(outputPath))
{
    if (check.Count != 27) throw new Exception($"Unexpected resource count {check.Count}");
    foreach (var b in buffs)
    {
        var key = new ResourceKey((ResourceType)0x6017E896, 0x00000000, b.Id);
        if (!check.Keys.Contains(key)) throw new Exception($"Missing buff {b.File}");
    }
    Console.WriteLine($"validated package resources: {check.Count}");
}
Console.WriteLine(outputPath);
