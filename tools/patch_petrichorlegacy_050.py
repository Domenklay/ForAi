from pathlib import Path
import re

root = Path(__file__).resolve().parents[1]
base = root / "PetrichorLegacy"

def rw(rel):
    p = base / rel
    return p, p.read_text(encoding="utf-8")

def save(p, text):
    p.write_text(text, encoding="utf-8")

# ---------- Talent catalog: 7 classes, 3 specs each ----------
p, t = rw("Progression/TalentCatalog.cs")

t = t.replace(
"        SeekerMerchant,\n        SeekerProspector,\n        SeekerRelicKeeper\n",
"        SeekerMerchant,\n        SeekerProspector,\n        SeekerRelicKeeper,\n        Arcanist,\n        ArcanistChronomancer,\n        ArcanistHexer,\n        ArcanistStormcaller,\n        Technomancer,\n        TechnomancerDroneMaster,\n        TechnomancerInterceptor,\n        TechnomancerConstructor,\n        Commander,\n        CommanderTactician,\n        CommanderStandardBearer,\n        CommanderWarlord\n")

# Move drone rewards away from tank/economy classes.
t = t.replace('new TalentDef("bastion_legendary", "Легенда: Защитные микроботы", "Финал подкласса: каждый забег начинается с 1 Defensive Microbots, сбивающего опасные снаряды.", TalentBranch.GuardianBastion, 1, 3, 45, "bastion_lastwall", 1, 1, 4)',
              'new TalentDef("bastion_legendary", "Легенда: Эгида", "Финал подкласса: каждый забег начинается с 1 Aegis — перелечение превращается в барьер.", TalentBranch.GuardianBastion, 1, 3, 45, "bastion_lastwall", 1, 1, 4)')
t = t.replace('new TalentDef("merchant_legendary", "Легенда: Запчасти дронов", "Финал подкласса: каждый забег начинается с 1 Spare Drone Parts.", TalentBranch.SeekerMerchant, 1, 3, 45, "merchant_capital", 1, 1, 4)',
              'new TalentDef("merchant_legendary", "Легенда: Военные облигации", "Финал подкласса: каждый забег начинается с 1 War Bonds — накопленное золото усиливает поддержку на боях с боссами.", TalentBranch.SeekerMerchant, 1, 3, 45, "merchant_capital", 1, 1, 4)')

anchor = '            new TalentDef("relic_legendary", "Легенда: Связанный душой катализатор", "Финал подкласса: каждый забег начинается с 1 Soulbound Catalyst.", TalentBranch.SeekerRelicKeeper, 1, 3, 45, "relic_attunement", 1, 1, 4)\n'
if anchor not in t:
    raise RuntimeError("Talent insertion anchor not found")
new_talents = r'''            ,

            // АРКАНИСТ — навыки, ротация и ослабление целей; почти без защиты.
            new TalentDef("arcanist_cooldown", "Поток эфира", "-1% времени восстановления навыков за ранг.", TalentBranch.Arcanist, 3, unlockLevel: 10, treeColumn: 1, treeRow: 0),
            new TalentDef("arcanist_damage", "Арканный импульс", "+1% урона за ранг.", TalentBranch.Arcanist, 3, unlockLevel: 10, prerequisiteId: "arcanist_cooldown", prerequisiteRank: 1, treeColumn: 0, treeRow: 1),
            new TalentDef("arcanist_attack", "Быстрый каст", "+1% скорости атаки за ранг.", TalentBranch.Arcanist, 3, unlockLevel: 10, prerequisiteId: "arcanist_cooldown", prerequisiteRank: 1, treeColumn: 2, treeRow: 1),
            new TalentDef("arcanist_move", "Скольжение", "+1.5% скорости движения за ранг.", TalentBranch.Arcanist, 2, unlockLevel: 12, prerequisiteId: "arcanist_damage", prerequisiteRank: 2, treeColumn: 0, treeRow: 2),
            new TalentDef("arcanist_crit", "Фокусировка", "+0.75% критического шанса за ранг.", TalentBranch.Arcanist, 2, unlockLevel: 12, prerequisiteId: "arcanist_attack", prerequisiteRank: 2, treeColumn: 2, treeRow: 2),
            new TalentDef("arcanist_convergence", "Схождение потоков", "+1% урона и -2% времени восстановления навыков.", TalentBranch.Arcanist, 1, 2, 15, "arcanist_move", 2, 1, 3),
            new TalentDef("arcanist_void_capstone", "Лизатная ячейка", "Классовый фиолетовый финал: каждый забег начинается с 1 Lysate Cell.", TalentBranch.Arcanist, 1, 3, 18, "arcanist_convergence", 1, 1, 4),

            // АРКАНИСТ / ХРОНОМАНТ — самая гибкая ротация навыков, но без защитной страховки.
            new TalentDef("chrono_cooldown", "Сжатие времени", "-1.5% времени восстановления навыков за ранг.", TalentBranch.ArcanistChronomancer, 3, unlockLevel: 20, treeColumn: 1, treeRow: 0),
            new TalentDef("chrono_attack", "Ускорение", "+1.5% скорости атаки за ранг.", TalentBranch.ArcanistChronomancer, 2, unlockLevel: 20, prerequisiteId: "chrono_cooldown", prerequisiteRank: 1, treeColumn: 0, treeRow: 1),
            new TalentDef("chrono_move", "Сдвиг фазы", "+1.5% скорости движения за ранг.", TalentBranch.ArcanistChronomancer, 2, unlockLevel: 20, prerequisiteId: "chrono_cooldown", prerequisiteRank: 1, treeColumn: 2, treeRow: 1),
            new TalentDef("chrono_damage", "Повторный импульс", "+1% урона за ранг.", TalentBranch.ArcanistChronomancer, 2, unlockLevel: 25, prerequisiteId: "chrono_attack", prerequisiteRank: 2, treeColumn: 0, treeRow: 2),
            new TalentDef("chrono_overclock", "Вне времени", "+2% скорости атаки и -2% времени восстановления навыков.", TalentBranch.ArcanistChronomancer, 1, 2, 35, "chrono_damage", 2, 1, 3),
            new TalentDef("chrono_legendary", "Легенда: Мозговые стебли", "Финал подкласса: каждый забег начинается с 1 Brainstalks.", TalentBranch.ArcanistChronomancer, 1, 3, 45, "chrono_overclock", 1, 1, 4),

            // АРКАНИСТ / ПРОКЛИНАТЕЛЬ — сильнее против уже опасных и редких целей.
            new TalentDef("hex_damage", "Порча", "+1% урона за ранг.", TalentBranch.ArcanistHexer, 3, unlockLevel: 20, treeColumn: 1, treeRow: 0),
            new TalentDef("hex_cooldown", "Зловещий ритм", "-1% времени восстановления навыков за ранг.", TalentBranch.ArcanistHexer, 2, unlockLevel: 20, prerequisiteId: "hex_damage", prerequisiteRank: 1, treeColumn: 0, treeRow: 1),
            new TalentDef("hex_crit", "Слабое место", "+0.75% критического шанса за ранг.", TalentBranch.ArcanistHexer, 2, unlockLevel: 20, prerequisiteId: "hex_damage", prerequisiteRank: 1, treeColumn: 2, treeRow: 1),
            new TalentDef("hex_hunt", "Печать охоты", "+2% урона боссам и особым монстрам за ранг.", TalentBranch.ArcanistHexer, 2, unlockLevel: 25, prerequisiteId: "hex_cooldown", prerequisiteRank: 2, treeColumn: 0, treeRow: 2),
            new TalentDef("hex_corrosion", "Разъедающая печать", "Ещё +3% урона боссам и особым монстрам.", TalentBranch.ArcanistHexer, 1, 2, 35, "hex_hunt", 2, 1, 3),
            new TalentDef("hex_legendary", "Легенда: Симбиотический скорпион", "Финал подкласса: каждый забег начинается с 1 Symbiotic Scorpion.", TalentBranch.ArcanistHexer, 1, 3, 45, "hex_corrosion", 1, 1, 4),

            // АРКАНИСТ / БУРЕВЕСТНИК — темп, атаки и зачистка пачек.
            new TalentDef("storm_attack", "Грозовой темп", "+1.5% скорости атаки за ранг.", TalentBranch.ArcanistStormcaller, 3, unlockLevel: 20, treeColumn: 1, treeRow: 0),
            new TalentDef("storm_move", "Порыв ветра", "+1.5% скорости движения за ранг.", TalentBranch.ArcanistStormcaller, 2, unlockLevel: 20, prerequisiteId: "storm_attack", prerequisiteRank: 1, treeColumn: 0, treeRow: 1),
            new TalentDef("storm_damage", "Разряд", "+1% урона за ранг.", TalentBranch.ArcanistStormcaller, 2, unlockLevel: 20, prerequisiteId: "storm_attack", prerequisiteRank: 1, treeColumn: 2, treeRow: 1),
            new TalentDef("storm_cooldown", "Грозовой цикл", "-1% времени восстановления навыков за ранг.", TalentBranch.ArcanistStormcaller, 2, unlockLevel: 25, prerequisiteId: "storm_move", prerequisiteRank: 2, treeColumn: 0, treeRow: 2),
            new TalentDef("storm_charge", "Перегрузка", "+2% скорости атаки и +1% урона.", TalentBranch.ArcanistStormcaller, 1, 2, 35, "storm_cooldown", 2, 1, 3),
            new TalentDef("storm_legendary", "Легенда: Резонансный диск", "Финал подкласса: каждый забег начинается с 1 Resonance Disc.", TalentBranch.ArcanistStormcaller, 1, 3, 45, "storm_charge", 1, 1, 4),

            // ТЕХНОМАНТ — стеклянный класс: скорость и внешняя огневая мощь вместо собственной защиты.
            new TalentDef("tech_attack", "Разогнанные сервоприводы", "+1.5% скорости атаки за ранг.", TalentBranch.Technomancer, 3, unlockLevel: 10, treeColumn: 1, treeRow: 0),
            new TalentDef("tech_move", "Лёгкое шасси", "+1.5% скорости движения за ранг.", TalentBranch.Technomancer, 3, unlockLevel: 10, prerequisiteId: "tech_attack", prerequisiteRank: 1, treeColumn: 0, treeRow: 1),
            new TalentDef("tech_cooldown", "Контур управления", "-1% времени восстановления навыков за ранг.", TalentBranch.Technomancer, 2, unlockLevel: 10, prerequisiteId: "tech_attack", prerequisiteRank: 1, treeColumn: 2, treeRow: 1),
            new TalentDef("tech_minion_damage", "Боевой протокол", "+5% урона подконтрольных существ за ранг.", TalentBranch.Technomancer, 2, unlockLevel: 12, prerequisiteId: "tech_move", prerequisiteRank: 2, treeColumn: 0, treeRow: 2),
            new TalentDef("tech_minion_health", "Усиленные корпуса", "+5% здоровья подконтрольных существ за ранг.", TalentBranch.Technomancer, 2, unlockLevel: 12, prerequisiteId: "tech_cooldown", prerequisiteRank: 2, treeColumn: 2, treeRow: 2),
            new TalentDef("tech_core", "Сетевая синхронизация", "+2% скорости атаки и движения владельца; +5% урона миньонов.", TalentBranch.Technomancer, 1, 2, 15, "tech_minion_damage", 2, 1, 3),
            new TalentDef("tech_void_capstone", "Плазменная креветка", "Классовый фиолетовый финал: каждый забег начинается с 1 Plasma Shrimp.", TalentBranch.Technomancer, 1, 3, 18, "tech_core", 1, 1, 4),

            // ТЕХНОМАНТ / ДРОНОВОД — максимум силы переносится на дронов и миньонов.
            new TalentDef("drone_damage", "Боевые прошивки", "+6% урона подконтрольных существ за ранг.", TalentBranch.TechnomancerDroneMaster, 3, unlockLevel: 20, treeColumn: 1, treeRow: 0),
            new TalentDef("drone_health", "Резервные детали", "+6% здоровья подконтрольных существ за ранг.", TalentBranch.TechnomancerDroneMaster, 2, unlockLevel: 20, prerequisiteId: "drone_damage", prerequisiteRank: 1, treeColumn: 0, treeRow: 1),
            new TalentDef("drone_attack", "Синхронный огонь", "+5% скорости атаки подконтрольных существ за ранг.", TalentBranch.TechnomancerDroneMaster, 2, unlockLevel: 20, prerequisiteId: "drone_damage", prerequisiteRank: 1, treeColumn: 2, treeRow: 1),
            new TalentDef("drone_move", "Протокол преследования", "+5% скорости движения подконтрольных существ за ранг.", TalentBranch.TechnomancerDroneMaster, 2, unlockLevel: 25, prerequisiteId: "drone_health", prerequisiteRank: 2, treeColumn: 0, treeRow: 2),
            new TalentDef("drone_network", "Рой", "Подконтрольные существа получают ещё +10% урона.", TalentBranch.TechnomancerDroneMaster, 1, 2, 35, "drone_move", 2, 1, 3),
            new TalentDef("drone_legendary", "Легенда: Запчасти дронов", "Финал подкласса: каждый забег начинается с 1 Spare Drone Parts.", TalentBranch.TechnomancerDroneMaster, 1, 3, 45, "drone_network", 1, 1, 4),

            // ТЕХНОМАНТ / ПЕРЕХВАТЧИК — сам хрупкий, но быстрее и защищён автоматической ПРО.
            new TalentDef("interceptor_attack", "Система наведения", "+1.5% скорости атаки за ранг.", TalentBranch.TechnomancerInterceptor, 3, unlockLevel: 20, treeColumn: 1, treeRow: 0),
            new TalentDef("interceptor_move", "Уклоняющее шасси", "+1.5% скорости движения за ранг.", TalentBranch.TechnomancerInterceptor, 2, unlockLevel: 20, prerequisiteId: "interceptor_attack", prerequisiteRank: 1, treeColumn: 0, treeRow: 1),
            new TalentDef("interceptor_cooldown", "Быстрый цикл", "-1% времени восстановления навыков за ранг.", TalentBranch.TechnomancerInterceptor, 2, unlockLevel: 20, prerequisiteId: "interceptor_attack", prerequisiteRank: 1, treeColumn: 2, treeRow: 1),
            new TalentDef("interceptor_damage", "Ответный импульс", "+1% урона за ранг.", TalentBranch.TechnomancerInterceptor, 2, unlockLevel: 25, prerequisiteId: "interceptor_move", prerequisiteRank: 2, treeColumn: 0, treeRow: 2),
            new TalentDef("interceptor_matrix", "Матрица перехвата", "+2% скорости атаки и движения.", TalentBranch.TechnomancerInterceptor, 1, 2, 35, "interceptor_damage", 2, 1, 3),
            new TalentDef("interceptor_legendary", "Легенда: Защитные микроботы", "Финал подкласса: каждый забег начинается с 1 Defensive Microbots.", TalentBranch.TechnomancerInterceptor, 1, 3, 45, "interceptor_matrix", 1, 1, 4),

            // ТЕХНОМАНТ / КОНСТРУКТОР — один сильный компаньон и усиление механических союзников.
            new TalentDef("constructor_minion_damage", "Силовое ядро", "+5% урона подконтрольных существ за ранг.", TalentBranch.TechnomancerConstructor, 3, unlockLevel: 20, treeColumn: 1, treeRow: 0),
            new TalentDef("constructor_minion_health", "Утолщённый корпус", "+7% здоровья подконтрольных существ за ранг.", TalentBranch.TechnomancerConstructor, 2, unlockLevel: 20, prerequisiteId: "constructor_minion_damage", prerequisiteRank: 1, treeColumn: 0, treeRow: 1),
            new TalentDef("constructor_move", "Мобильная платформа", "+1.5% скорости движения владельца за ранг.", TalentBranch.TechnomancerConstructor, 2, unlockLevel: 20, prerequisiteId: "constructor_minion_damage", prerequisiteRank: 1, treeColumn: 2, treeRow: 1),
            new TalentDef("constructor_cooldown", "Сборочный цикл", "-1% времени восстановления навыков за ранг.", TalentBranch.TechnomancerConstructor, 2, unlockLevel: 25, prerequisiteId: "constructor_minion_health", prerequisiteRank: 2, treeColumn: 0, treeRow: 2),
            new TalentDef("constructor_core", "Прототип", "Подконтрольные существа получают +10% скорости атаки и движения.", TalentBranch.TechnomancerConstructor, 1, 2, 35, "constructor_cooldown", 2, 1, 3),
            new TalentDef("constructor_legendary", "Легенда: Осиротевшее ядро", "Финал подкласса: каждый забег начинается с 1 Orphaned Core.", TalentBranch.TechnomancerConstructor, 1, 3, 45, "constructor_core", 1, 1, 4),

            // КОМАНДИР — универсальная тактика, метки целей и союзники; не превосходит специализированные классы в их нишах.
            new TalentDef("commander_damage", "Боевой приказ", "+1% урона за ранг.", TalentBranch.Commander, 3, unlockLevel: 10, treeColumn: 1, treeRow: 0),
            new TalentDef("commander_move", "Манёвр", "+1% скорости движения за ранг.", TalentBranch.Commander, 2, unlockLevel: 10, prerequisiteId: "commander_damage", prerequisiteRank: 1, treeColumn: 0, treeRow: 1),
            new TalentDef("commander_attack", "Темп отряда", "+1% скорости атаки за ранг.", TalentBranch.Commander, 2, unlockLevel: 10, prerequisiteId: "commander_damage", prerequisiteRank: 1, treeColumn: 2, treeRow: 1),
            new TalentDef("commander_armor", "Дисциплина", "+1 брони за ранг.", TalentBranch.Commander, 2, unlockLevel: 12, prerequisiteId: "commander_move", prerequisiteRank: 1, treeColumn: 0, treeRow: 2),
            new TalentDef("commander_priority", "Приоритетная цель", "+2% урона боссам и особым монстрам за ранг.", TalentBranch.Commander, 2, unlockLevel: 12, prerequisiteId: "commander_attack", prerequisiteRank: 1, treeColumn: 2, treeRow: 2),
            new TalentDef("commander_order", "Слаженность", "+1% урона, скорости атаки и движения.", TalentBranch.Commander, 1, 2, 15, "commander_priority", 2, 1, 3),
            new TalentDef("commander_void_capstone", "Сингулярная полоса", "Классовый фиолетовый финал: каждый забег начинается с 1 Singularity Band.", TalentBranch.Commander, 1, 3, 18, "commander_order", 1, 1, 4),

            // КОМАНДИР / ТАКТИК — сильнее против приоритетных целей, но слабее Палача по чистому DPS.
            new TalentDef("tactician_boss", "Разбор цели", "+2% урона боссам за ранг.", TalentBranch.CommanderTactician, 3, unlockLevel: 20, treeColumn: 1, treeRow: 0),
            new TalentDef("tactician_rare", "Опасная цель", "+2% урона особым монстрам за ранг.", TalentBranch.CommanderTactician, 2, unlockLevel: 20, prerequisiteId: "tactician_boss", prerequisiteRank: 1, treeColumn: 0, treeRow: 1),
            new TalentDef("tactician_crit", "Окно атаки", "+0.75% критического шанса за ранг.", TalentBranch.CommanderTactician, 2, unlockLevel: 20, prerequisiteId: "tactician_boss", prerequisiteRank: 1, treeColumn: 2, treeRow: 1),
            new TalentDef("tactician_move", "Перестроение", "+1% скорости движения за ранг.", TalentBranch.CommanderTactician, 2, unlockLevel: 25, prerequisiteId: "tactician_rare", prerequisiteRank: 2, treeColumn: 0, treeRow: 2),
            new TalentDef("tactician_mark", "Отмеченная цель", "Ещё +3% урона боссам и особым монстрам.", TalentBranch.CommanderTactician, 1, 2, 35, "tactician_move", 2, 1, 3),
            new TalentDef("tactician_legendary", "Легенда: Нектар роста", "Финал подкласса: каждый забег начинается с 1 Growth Nectar.", TalentBranch.CommanderTactician, 1, 3, 45, "tactician_mark", 1, 1, 4),

            // КОМАНДИР / ЗНАМЕНОСЕЦ — умеренная универсальная аура без танковой специализации.
            new TalentDef("standard_health", "Знамя стойкости", "+1% максимального здоровья за ранг.", TalentBranch.CommanderStandardBearer, 2, unlockLevel: 20, treeColumn: 1, treeRow: 0),
            new TalentDef("standard_attack", "Знамя натиска", "+1.5% скорости атаки за ранг.", TalentBranch.CommanderStandardBearer, 2, unlockLevel: 20, prerequisiteId: "standard_health", prerequisiteRank: 1, treeColumn: 0, treeRow: 1),
            new TalentDef("standard_move", "Знамя манёвра", "+1.5% скорости движения за ранг.", TalentBranch.CommanderStandardBearer, 2, unlockLevel: 20, prerequisiteId: "standard_health", prerequisiteRank: 1, treeColumn: 2, treeRow: 1),
            new TalentDef("standard_armor", "Удерживать строй", "+1 брони за ранг.", TalentBranch.CommanderStandardBearer, 2, unlockLevel: 25, prerequisiteId: "standard_attack", prerequisiteRank: 2, treeColumn: 0, treeRow: 2),
            new TalentDef("standard_banner", "Боевой штандарт", "+1% урона, скорости атаки и движения.", TalentBranch.CommanderStandardBearer, 1, 2, 35, "standard_armor", 2, 1, 3),
            new TalentDef("standard_legendary", "Легенда: Межзвёздное растение", "Финал подкласса: каждый забег начинается с 1 Interstellar Desk Plant.", TalentBranch.CommanderStandardBearer, 1, 3, 45, "standard_banner", 1, 1, 4),

            // КОМАНДИР / ПОЛКОВОДЕЦ — армия призванных союзников; слабее Техноманта в чистом усилении дронов.
            new TalentDef("warlord_minion_damage", "Боевой строй", "+4% урона подконтрольных существ за ранг.", TalentBranch.CommanderWarlord, 3, unlockLevel: 20, treeColumn: 1, treeRow: 0),
            new TalentDef("warlord_minion_health", "Резерв", "+4% здоровья подконтрольных существ за ранг.", TalentBranch.CommanderWarlord, 2, unlockLevel: 20, prerequisiteId: "warlord_minion_damage", prerequisiteRank: 1, treeColumn: 0, treeRow: 1),
            new TalentDef("warlord_damage", "Личный пример", "+1% урона владельца за ранг.", TalentBranch.CommanderWarlord, 2, unlockLevel: 20, prerequisiteId: "warlord_minion_damage", prerequisiteRank: 1, treeColumn: 2, treeRow: 1),
            new TalentDef("warlord_move", "Марш", "+1.5% скорости движения владельца за ранг.", TalentBranch.CommanderWarlord, 2, unlockLevel: 25, prerequisiteId: "warlord_minion_health", prerequisiteRank: 2, treeColumn: 0, treeRow: 2),
            new TalentDef("warlord_army", "Армия", "Подконтрольные существа получают +8% скорости атаки.", TalentBranch.CommanderWarlord, 1, 2, 35, "warlord_move", 2, 1, 3),
            new TalentDef("warlord_legendary", "Легенда: Счастливая маска", "Финал подкласса: каждый забег начинается с 1 Happiest Mask.", TalentBranch.CommanderWarlord, 1, 3, 45, "warlord_army", 1, 1, 4)
'''
t = t.replace(anchor, anchor + new_talents)

# Branch -> class/spec mappings.
t = t.replace('                case TalentBranch.SeekerRelicKeeper: return "Seeker";\n                default: return string.Empty;',
'''                case TalentBranch.SeekerRelicKeeper: return "Seeker";
                case TalentBranch.Arcanist:
                case TalentBranch.ArcanistChronomancer:
                case TalentBranch.ArcanistHexer:
                case TalentBranch.ArcanistStormcaller: return "Arcanist";
                case TalentBranch.Technomancer:
                case TalentBranch.TechnomancerDroneMaster:
                case TalentBranch.TechnomancerInterceptor:
                case TalentBranch.TechnomancerConstructor: return "Technomancer";
                case TalentBranch.Commander:
                case TalentBranch.CommanderTactician:
                case TalentBranch.CommanderStandardBearer:
                case TalentBranch.CommanderWarlord: return "Commander";
                default: return string.Empty;''')
t = t.replace('                case TalentBranch.SeekerRelicKeeper: return "RelicKeeper";\n                default: return string.Empty;',
'''                case TalentBranch.SeekerRelicKeeper: return "RelicKeeper";
                case TalentBranch.ArcanistChronomancer: return "Chronomancer";
                case TalentBranch.ArcanistHexer: return "Hexer";
                case TalentBranch.ArcanistStormcaller: return "Stormcaller";
                case TalentBranch.TechnomancerDroneMaster: return "DroneMaster";
                case TalentBranch.TechnomancerInterceptor: return "Interceptor";
                case TalentBranch.TechnomancerConstructor: return "Constructor";
                case TalentBranch.CommanderTactician: return "Tactician";
                case TalentBranch.CommanderStandardBearer: return "StandardBearer";
                case TalentBranch.CommanderWarlord: return "Warlord";
                default: return string.Empty;''')
save(p, t)

# ---------- Mastery for new classes ----------
p, m = rw("Progression/MasteryCatalog.cs")
anchor = '            new MasteryDef("mastery_seeker_startgold", "Капитал", "+0.15 стартового золота за эффективный ранг.", "Seeker", 0.15f)\n'
if anchor not in m:
    raise RuntimeError("Mastery anchor not found")
extra = r'''            ,
            new MasteryDef("mastery_arcanist_damage", "Арканная мощь", "+0.10% урона за эффективный ранг.", "Arcanist", 0.0010f),
            new MasteryDef("mastery_arcanist_attack", "Быстрый каст", "+0.12% скорости атаки за эффективный ранг.", "Arcanist", 0.0012f),
            new MasteryDef("mastery_arcanist_cooldown", "Поток времени", "-0.05% времени восстановления за эффективный ранг.", "Arcanist", 0.0005f),
            new MasteryDef("mastery_arcanist_move", "Скольжение", "+0.10% скорости движения за эффективный ранг.", "Arcanist", 0.0010f),

            new MasteryDef("mastery_tech_attack", "Сервоприводы", "+0.12% скорости атаки владельца за эффективный ранг.", "Technomancer", 0.0012f),
            new MasteryDef("mastery_tech_move", "Лёгкое шасси", "+0.12% скорости движения владельца за эффективный ранг.", "Technomancer", 0.0012f),
            new MasteryDef("mastery_tech_minion_damage", "Боевые алгоритмы", "+0.30% урона миньонов за эффективный ранг.", "Technomancer", 0.0030f),
            new MasteryDef("mastery_tech_minion_health", "Усиленные корпуса", "+0.30% здоровья миньонов за эффективный ранг.", "Technomancer", 0.0030f),

            new MasteryDef("mastery_commander_damage", "Приказ на огонь", "+0.10% урона за эффективный ранг.", "Commander", 0.0010f),
            new MasteryDef("mastery_commander_move", "Манёвр", "+0.10% скорости движения за эффективный ранг.", "Commander", 0.0010f),
            new MasteryDef("mastery_commander_armor", "Дисциплина", "+0.12 брони за эффективный ранг.", "Commander", 0.12f),
            new MasteryDef("mastery_commander_minion", "Командование", "+0.20% урона миньонов за эффективный ранг.", "Commander", 0.0020f)
'''
m = m.replace(anchor, anchor + extra)
save(p, m)

# ---------- Class/spec validation ----------
p, prog = rw("Progression/ProgressionService.cs")
prog = prog.replace('            if (classId != "Guardian" && classId != "Slayer" && classId != "Pathfinder" && classId != "Seeker")',
                    '            if (classId != "Guardian" && classId != "Slayer" && classId != "Pathfinder" && classId != "Seeker" && classId != "Arcanist" && classId != "Technomancer" && classId != "Commander")')
prog = prog.replace('                case "Seeker": return specId == "Merchant" || specId == "Prospector" || specId == "RelicKeeper";\n                default: return false;',
'''                case "Seeker": return specId == "Merchant" || specId == "Prospector" || specId == "RelicKeeper";
                case "Arcanist": return specId == "Chronomancer" || specId == "Hexer" || specId == "Stormcaller";
                case "Technomancer": return specId == "DroneMaster" || specId == "Interceptor" || specId == "Constructor";
                case "Commander": return specId == "Tactician" || specId == "StandardBearer" || specId == "Warlord";
                default: return false;''')
save(p, prog)

p, net = rw("Networking/ProgressionNetwork.cs")
net = net.replace('            classId == "Guardian" || classId == "Slayer" || classId == "Pathfinder" || classId == "Seeker";',
                  '            classId == "Guardian" || classId == "Slayer" || classId == "Pathfinder" || classId == "Seeker" || classId == "Arcanist" || classId == "Technomancer" || classId == "Commander";')
net = net.replace('host/single-player authoritative in v0.4.0', 'host/single-player authoritative in v0.5.0')
save(p, net)

# ---------- Capstone rewards, all unique ----------
p, cap = rw("Progression/CapstoneRewardSystem.cs")
cap = cap.replace('new RewardDef { TalentId = "guardian_void_capstone", DisplayName = "Safer Spaces", ItemCandidates = new[] { "BearVoid" } },',
                  'new RewardDef { TalentId = "guardian_void_capstone", DisplayName = "Safer Spaces", ItemCandidates = new[] { "BearVoid" } },')
cap = cap.replace('new RewardDef { TalentId = "seeker_void_capstone", DisplayName = "Encrusted Key", ItemCandidates = new[] { "TreasureCacheVoid" } }',
'''new RewardDef { TalentId = "seeker_void_capstone", DisplayName = "Encrusted Key", ItemCandidates = new[] { "TreasureCacheVoid" } },
            new RewardDef { TalentId = "arcanist_void_capstone", DisplayName = "Lysate Cell", ItemCandidates = new[] { "EquipmentMagazineVoid" } },
            new RewardDef { TalentId = "tech_void_capstone", DisplayName = "Plasma Shrimp", ItemCandidates = new[] { "MissileVoid" } },
            new RewardDef { TalentId = "commander_void_capstone", DisplayName = "Singularity Band", ItemCandidates = new[] { "ElementalRingVoid" } }''')
cap = cap.replace('new RewardDef { TalentId = "bastion_legendary", DisplayName = "Defensive Microbots", ItemCandidates = new[] { "CaptainDefenseMatrix" } },',
                  'new RewardDef { TalentId = "bastion_legendary", DisplayName = "Aegis", ItemCandidates = new[] { "BarrierOnOverHeal" } },')
cap = cap.replace('new RewardDef { TalentId = "merchant_legendary", DisplayName = "Spare Drone Parts", ItemCandidates = new[] { "DroneWeapons" } },',
                  'new RewardDef { TalentId = "merchant_legendary", DisplayName = "War Bonds", ItemCandidates = new[] { "BarrageOnBoss" } },')
cap = cap.replace('new RewardDef { TalentId = "relic_legendary", DisplayName = "Soulbound Catalyst", ItemCandidates = new[] { "Talisman" } }',
'''new RewardDef { TalentId = "relic_legendary", DisplayName = "Soulbound Catalyst", ItemCandidates = new[] { "Talisman" } },
            new RewardDef { TalentId = "chrono_legendary", DisplayName = "Brainstalks", ItemCandidates = new[] { "KillEliteFrenzy" } },
            new RewardDef { TalentId = "hex_legendary", DisplayName = "Symbiotic Scorpion", ItemCandidates = new[] { "PermanentDebuffOnHit" } },
            new RewardDef { TalentId = "storm_legendary", DisplayName = "Resonance Disc", ItemCandidates = new[] { "LaserTurbine" } },
            new RewardDef { TalentId = "drone_legendary", DisplayName = "Spare Drone Parts", ItemCandidates = new[] { "DroneWeapons" } },
            new RewardDef { TalentId = "interceptor_legendary", DisplayName = "Defensive Microbots", ItemCandidates = new[] { "CaptainDefenseMatrix" } },
            new RewardDef { TalentId = "constructor_legendary", DisplayName = "Orphaned Core", ItemCandidates = new[] { "PhysicsProjectile" } },
            new RewardDef { TalentId = "tactician_legendary", DisplayName = "Growth Nectar", ItemCandidates = new[] { "BoostAllStats" } },
            new RewardDef { TalentId = "standard_legendary", DisplayName = "Interstellar Desk Plant", ItemCandidates = new[] { "Plant" } },
            new RewardDef { TalentId = "warlord_legendary", DisplayName = "Happiest Mask", ItemCandidates = new[] { "GhostOnKill" } }''')
save(p, cap)

# ---------- Runtime stats and minion scaling ----------
p, add = rw("Progression/AdditionalSpecEffects.cs")
needle = '            if (self == null || self.master == null || self.master.playerCharacterMasterController == null) return;\n            if (ServerProgressionState.Get(self.master) == null) return;\n'
replacement = r'''            if (self == null || self.master == null) return;

            // Minions inherit only the deliberately small minion bonuses of the active Technomancer/Commander build.
            if (self.master.playerCharacterMasterController == null)
            {
                var ownership = self.master.GetComponent<MinionOwnership>();
                var owner = ownership != null ? ownership.ownerMaster : null;
                if (owner == null || ServerProgressionState.Get(owner) == null) return;
                var dmg = 0f;
                var hp = 0f;
                var atk = 0f;
                var mov = 0f;
                dmg += ServerProgressionState.Rank(owner, "tech_minion_damage") * 0.05f;
                hp += ServerProgressionState.Rank(owner, "tech_minion_health") * 0.05f;
                if (ServerProgressionState.Rank(owner, "tech_core") > 0) dmg += 0.05f;
                dmg += ServerProgressionState.Rank(owner, "drone_damage") * 0.06f;
                hp += ServerProgressionState.Rank(owner, "drone_health") * 0.06f;
                atk += ServerProgressionState.Rank(owner, "drone_attack") * 0.05f;
                mov += ServerProgressionState.Rank(owner, "drone_move") * 0.05f;
                if (ServerProgressionState.Rank(owner, "drone_network") > 0) dmg += 0.10f;
                dmg += ServerProgressionState.Rank(owner, "constructor_minion_damage") * 0.05f;
                hp += ServerProgressionState.Rank(owner, "constructor_minion_health") * 0.07f;
                if (ServerProgressionState.Rank(owner, "constructor_core") > 0) { atk += 0.10f; mov += 0.10f; }
                dmg += ServerProgressionState.Rank(owner, "warlord_minion_damage") * 0.04f;
                hp += ServerProgressionState.Rank(owner, "warlord_minion_health") * 0.04f;
                if (ServerProgressionState.Rank(owner, "warlord_army") > 0) atk += 0.08f;
                dmg += ServerProgressionState.MasteryValue(owner, "mastery_tech_minion_damage");
                hp += ServerProgressionState.MasteryValue(owner, "mastery_tech_minion_health");
                dmg += ServerProgressionState.MasteryValue(owner, "mastery_commander_minion");
                self.damage *= 1f + dmg;
                self.maxHealth *= 1f + hp;
                self.attackSpeed *= 1f + atk;
                self.moveSpeed *= 1f + mov;
                return;
            }
            if (ServerProgressionState.Get(self.master) == null) return;
'''
if needle not in add:
    raise RuntimeError("AdditionalSpecEffects player guard not found")
add = add.replace(needle, replacement)
insert = r'''
            // Arcanist — skill-centric glass cannon.
            self.damage *= 1f + ServerProgressionState.Rank(self.master, "arcanist_damage") * 0.01f;
            self.attackSpeed *= 1f + ServerProgressionState.Rank(self.master, "arcanist_attack") * 0.01f;
            self.moveSpeed *= 1f + ServerProgressionState.Rank(self.master, "arcanist_move") * 0.015f;
            self.crit += ServerProgressionState.Rank(self.master, "arcanist_crit") * 0.75f;
            ApplyCooldownScale(self.skillLocator, ServerProgressionState.Rank(self.master, "arcanist_cooldown") * 0.01f);
            if (ServerProgressionState.Rank(self.master, "arcanist_convergence") > 0) { self.damage *= 1.01f; ApplyCooldownScale(self.skillLocator, 0.02f); }

            ApplyCooldownScale(self.skillLocator, ServerProgressionState.Rank(self.master, "chrono_cooldown") * 0.015f);
            self.attackSpeed *= 1f + ServerProgressionState.Rank(self.master, "chrono_attack") * 0.015f;
            self.moveSpeed *= 1f + ServerProgressionState.Rank(self.master, "chrono_move") * 0.015f;
            self.damage *= 1f + ServerProgressionState.Rank(self.master, "chrono_damage") * 0.01f;
            if (ServerProgressionState.Rank(self.master, "chrono_overclock") > 0) { self.attackSpeed *= 1.02f; ApplyCooldownScale(self.skillLocator, 0.02f); }

            self.damage *= 1f + ServerProgressionState.Rank(self.master, "hex_damage") * 0.01f;
            self.crit += ServerProgressionState.Rank(self.master, "hex_crit") * 0.75f;
            ApplyCooldownScale(self.skillLocator, ServerProgressionState.Rank(self.master, "hex_cooldown") * 0.01f);

            self.attackSpeed *= 1f + ServerProgressionState.Rank(self.master, "storm_attack") * 0.015f;
            self.moveSpeed *= 1f + ServerProgressionState.Rank(self.master, "storm_move") * 0.015f;
            self.damage *= 1f + ServerProgressionState.Rank(self.master, "storm_damage") * 0.01f;
            ApplyCooldownScale(self.skillLocator, ServerProgressionState.Rank(self.master, "storm_cooldown") * 0.01f);
            if (ServerProgressionState.Rank(self.master, "storm_charge") > 0) { self.attackSpeed *= 1.02f; self.damage *= 1.01f; }

            // Technomancer — personal stats stay light; most power is external.
            self.attackSpeed *= 1f + ServerProgressionState.Rank(self.master, "tech_attack") * 0.015f;
            self.moveSpeed *= 1f + ServerProgressionState.Rank(self.master, "tech_move") * 0.015f;
            ApplyCooldownScale(self.skillLocator, ServerProgressionState.Rank(self.master, "tech_cooldown") * 0.01f);
            if (ServerProgressionState.Rank(self.master, "tech_core") > 0) { self.attackSpeed *= 1.02f; self.moveSpeed *= 1.02f; }
            self.attackSpeed *= 1f + ServerProgressionState.Rank(self.master, "interceptor_attack") * 0.015f;
            self.moveSpeed *= 1f + ServerProgressionState.Rank(self.master, "interceptor_move") * 0.015f;
            self.damage *= 1f + ServerProgressionState.Rank(self.master, "interceptor_damage") * 0.01f;
            ApplyCooldownScale(self.skillLocator, ServerProgressionState.Rank(self.master, "interceptor_cooldown") * 0.01f);
            if (ServerProgressionState.Rank(self.master, "interceptor_matrix") > 0) { self.attackSpeed *= 1.02f; self.moveSpeed *= 1.02f; }
            self.moveSpeed *= 1f + ServerProgressionState.Rank(self.master, "constructor_move") * 0.015f;
            ApplyCooldownScale(self.skillLocator, ServerProgressionState.Rank(self.master, "constructor_cooldown") * 0.01f);

            // Commander — broad but deliberately smaller bonuses than dedicated classes.
            self.damage *= 1f + ServerProgressionState.Rank(self.master, "commander_damage") * 0.01f;
            self.moveSpeed *= 1f + ServerProgressionState.Rank(self.master, "commander_move") * 0.01f;
            self.attackSpeed *= 1f + ServerProgressionState.Rank(self.master, "commander_attack") * 0.01f;
            self.armor += ServerProgressionState.Rank(self.master, "commander_armor");
            if (ServerProgressionState.Rank(self.master, "commander_order") > 0) { self.damage *= 1.01f; self.moveSpeed *= 1.01f; self.attackSpeed *= 1.01f; }
            self.crit += ServerProgressionState.Rank(self.master, "tactician_crit") * 0.75f;
            self.moveSpeed *= 1f + ServerProgressionState.Rank(self.master, "tactician_move") * 0.01f;
            self.maxHealth *= 1f + ServerProgressionState.Rank(self.master, "standard_health") * 0.01f;
            self.attackSpeed *= 1f + ServerProgressionState.Rank(self.master, "standard_attack") * 0.015f;
            self.moveSpeed *= 1f + ServerProgressionState.Rank(self.master, "standard_move") * 0.015f;
            self.armor += ServerProgressionState.Rank(self.master, "standard_armor");
            if (ServerProgressionState.Rank(self.master, "standard_banner") > 0) { self.damage *= 1.01f; self.attackSpeed *= 1.01f; self.moveSpeed *= 1.01f; }
            self.damage *= 1f + ServerProgressionState.Rank(self.master, "warlord_damage") * 0.01f;
            self.moveSpeed *= 1f + ServerProgressionState.Rank(self.master, "warlord_move") * 0.015f;

            self.damage *= 1f + ServerProgressionState.MasteryValue(self.master, "mastery_arcanist_damage");
            self.attackSpeed *= 1f + ServerProgressionState.MasteryValue(self.master, "mastery_arcanist_attack");
            self.moveSpeed *= 1f + ServerProgressionState.MasteryValue(self.master, "mastery_arcanist_move");
            ApplyCooldownScale(self.skillLocator, ServerProgressionState.MasteryValue(self.master, "mastery_arcanist_cooldown"));
            self.attackSpeed *= 1f + ServerProgressionState.MasteryValue(self.master, "mastery_tech_attack");
            self.moveSpeed *= 1f + ServerProgressionState.MasteryValue(self.master, "mastery_tech_move");
            self.damage *= 1f + ServerProgressionState.MasteryValue(self.master, "mastery_commander_damage");
            self.moveSpeed *= 1f + ServerProgressionState.MasteryValue(self.master, "mastery_commander_move");
            self.armor += ServerProgressionState.MasteryValue(self.master, "mastery_commander_armor");
'''
needle2 = '            // Seeker / Relic Keeper — utility stats; the legendary reward handles equipment identity.\n'
if needle2 not in add:
    raise RuntimeError("AdditionalSpecEffects insertion anchor not found")
# Insert after existing Seeker block, before method closing. Easier: place before closing of player method.
method_end = '            if (ServerProgressionState.Rank(self.master, "relic_attunement") > 0)\n            {\n                self.moveSpeed *= 1.02f;\n                ApplyCooldownScale(self.skillLocator, 0.02f);\n            }\n'
if method_end not in add:
    raise RuntimeError("AdditionalSpecEffects method end anchor not found")
add = add.replace(method_end, method_end + insert)
save(p, add)

# ---------- Damage-vs-priority-target effects ----------
p, te = rw("Progression/TalentEffects.cs")
needle = '                if (victimBody.GetComponent<MonsterRarityMarker>() != null &&\n                    ServerProgressionState.Perfection(attackerBody.master, "perfection_prestige_predator") > 0)\n                    damageInfo.damage *= 1.02f;\n'
extra = r'''                var special = victimBody.GetComponent<MonsterRarityMarker>() != null;
                var boss = victimBody.isBoss;
                if (boss || special)
                {
                    damageInfo.damage *= 1f + ServerProgressionState.Rank(attackerBody.master, "hex_hunt") * 0.02f;
                    if (ServerProgressionState.Rank(attackerBody.master, "hex_corrosion") > 0) damageInfo.damage *= 1.03f;
                    damageInfo.damage *= 1f + ServerProgressionState.Rank(attackerBody.master, "commander_priority") * 0.02f;
                    if (boss) damageInfo.damage *= 1f + ServerProgressionState.Rank(attackerBody.master, "tactician_boss") * 0.02f;
                    if (special) damageInfo.damage *= 1f + ServerProgressionState.Rank(attackerBody.master, "tactician_rare") * 0.02f;
                    if (ServerProgressionState.Rank(attackerBody.master, "tactician_mark") > 0) damageInfo.damage *= 1.03f;
                }
'''
if needle not in te:
    raise RuntimeError("TalentEffects damage anchor not found")
te = te.replace(needle, needle + extra)
save(p, te)

# ---------- UI: 8 class buttons in two rows, branch mappings, labels/icons ----------
p, ui = rw("UI/MetaProgressionUIV5.cs")
old = '            var categories = new[] { TalentBranch.Legacy, TalentBranch.Guardian, TalentBranch.Slayer, TalentBranch.Pathfinder, TalentBranch.Seeker };\n            var y = area.y + 7f;\n            var w = (area.width - 14f) / categories.Length;\n            for (var i = 0; i < categories.Length; i++)\n            {\n                var branch = categories[i];\n                var selected = SameCategory(_selectedBranch, branch);\n                if (GUI.Toggle(new Rect(area.x + 7f + i * w, y, w - 5f, 31f), selected, BranchTitle(branch), "Button") && !SameCategory(_selectedBranch, branch))\n                {\n                    _selectedBranch = branch;\n                    _pendingSpecId = string.Empty;\n                    _treeScroll = Vector2.zero;\n                }\n            }\n\n            var page = new Rect(area.x + 7f, area.y + 44f, area.width - 14f, area.height - 51f);'
new = '''            var categories = new[] { TalentBranch.Legacy, TalentBranch.Guardian, TalentBranch.Slayer, TalentBranch.Pathfinder, TalentBranch.Seeker, TalentBranch.Arcanist, TalentBranch.Technomancer, TalentBranch.Commander };
            var y = area.y + 7f;
            const int cols = 4;
            var w = (area.width - 14f) / cols;
            for (var i = 0; i < categories.Length; i++)
            {
                var branch = categories[i];
                var selected = SameCategory(_selectedBranch, branch);
                var row = i / cols;
                var col = i % cols;
                if (GUI.Toggle(new Rect(area.x + 7f + col * w, y + row * 34f, w - 5f, 31f), selected, BranchTitle(branch), "Button") && !SameCategory(_selectedBranch, branch))
                {
                    _selectedBranch = branch;
                    _pendingSpecId = string.Empty;
                    _treeScroll = Vector2.zero;
                }
            }

            var page = new Rect(area.x + 7f, area.y + 78f, area.width - 14f, area.height - 85f);'''
if old not in ui:
    raise RuntimeError("UI category block not found")
ui = ui.replace(old, new)

ui = ui.replace('            if (id == "Pathfinder") return TalentBranch.Pathfinder;\n            return TalentBranch.Seeker;',
'''            if (id == "Pathfinder") return TalentBranch.Pathfinder;
            if (id == "Seeker") return TalentBranch.Seeker;
            if (id == "Arcanist") return TalentBranch.Arcanist;
            if (id == "Technomancer") return TalentBranch.Technomancer;
            return TalentBranch.Commander;''')
ui = ui.replace('            if (id == "Pathfinder") return TalentBranch.PathfinderScout;\n            return TalentBranch.SeekerMerchant;',
'''            if (id == "Pathfinder") return TalentBranch.PathfinderScout;
            if (id == "Seeker") return TalentBranch.SeekerMerchant;
            if (id == "Arcanist") return TalentBranch.ArcanistChronomancer;
            if (id == "Technomancer") return TalentBranch.TechnomancerDroneMaster;
            return TalentBranch.CommanderTactician;''')
ui = ui.replace('            if (id == "Pathfinder") return TalentBranch.PathfinderAcrobat;\n            return TalentBranch.SeekerProspector;',
'''            if (id == "Pathfinder") return TalentBranch.PathfinderAcrobat;
            if (id == "Seeker") return TalentBranch.SeekerProspector;
            if (id == "Arcanist") return TalentBranch.ArcanistHexer;
            if (id == "Technomancer") return TalentBranch.TechnomancerInterceptor;
            return TalentBranch.CommanderStandardBearer;''')
ui = ui.replace('            if (id == "Pathfinder") return TalentBranch.PathfinderSaboteur;\n            return TalentBranch.SeekerRelicKeeper;',
'''            if (id == "Pathfinder") return TalentBranch.PathfinderSaboteur;
            if (id == "Seeker") return TalentBranch.SeekerRelicKeeper;
            if (id == "Arcanist") return TalentBranch.ArcanistStormcaller;
            if (id == "Technomancer") return TalentBranch.TechnomancerConstructor;
            return TalentBranch.CommanderWarlord;''')

ui = ui.replace('                case TalentBranch.SeekerProspector: return "СТАРАТЕЛЬ";\n                default: return "РЕЛИКВАРИЙ";',
'''                case TalentBranch.SeekerProspector: return "СТАРАТЕЛЬ";
                case TalentBranch.SeekerRelicKeeper: return "РЕЛИКВАРИЙ";
                case TalentBranch.Arcanist: return "АРКАНИСТ";
                case TalentBranch.ArcanistChronomancer: return "ХРОНОМАНТ";
                case TalentBranch.ArcanistHexer: return "ПРОКЛИНАТЕЛЬ";
                case TalentBranch.ArcanistStormcaller: return "БУРЕВЕСТНИК";
                case TalentBranch.Technomancer: return "ТЕХНОМАНТ";
                case TalentBranch.TechnomancerDroneMaster: return "ДРОНОВОД";
                case TalentBranch.TechnomancerInterceptor: return "ПЕРЕХВАТЧИК";
                case TalentBranch.TechnomancerConstructor: return "КОНСТРУКТОР";
                case TalentBranch.Commander: return "КОМАНДИР";
                case TalentBranch.CommanderTactician: return "ТАКТИК";
                case TalentBranch.CommanderStandardBearer: return "ЗНАМЕНОСЕЦ";
                case TalentBranch.CommanderWarlord: return "ПОЛКОВОДЕЦ";
                default: return branch.ToString().ToUpperInvariant();''')
ui = ui.replace('            if (id == "Seeker") return "Искатель";\n            return "не выбран";',
'''            if (id == "Seeker") return "Искатель";
            if (id == "Arcanist") return "Арканист";
            if (id == "Technomancer") return "Техномант";
            if (id == "Commander") return "Командир";
            return "не выбран";''')
ui = ui.replace('            if (id == "RelicKeeper") return "Реликварий";\n            return "не выбрана";',
'''            if (id == "RelicKeeper") return "Реликварий";
            if (id == "Chronomancer") return "Хрономант";
            if (id == "Hexer") return "Проклинатель";
            if (id == "Stormcaller") return "Буревестник";
            if (id == "DroneMaster") return "Дроновод";
            if (id == "Interceptor") return "Перехватчик";
            if (id == "Constructor") return "Конструктор";
            if (id == "Tactician") return "Тактик";
            if (id == "StandardBearer") return "Знаменосец";
            if (id == "Warlord") return "Полководец";
            return "не выбрана";''')

# New capstone icons and semantic pools.
icon_anchor = '            if (id.Contains("relic_legendary")) return new[] { "Talisman" };\n'
icon_extra = '''            if (id.Contains("chrono_legendary")) return new[] { "KillEliteFrenzy" };
            if (id.Contains("hex_legendary")) return new[] { "PermanentDebuffOnHit" };
            if (id.Contains("storm_legendary")) return new[] { "LaserTurbine" };
            if (id.Contains("drone_legendary")) return new[] { "DroneWeapons" };
            if (id.Contains("interceptor_legendary")) return new[] { "CaptainDefenseMatrix" };
            if (id.Contains("constructor_legendary")) return new[] { "PhysicsProjectile" };
            if (id.Contains("tactician_legendary")) return new[] { "BoostAllStats" };
            if (id.Contains("standard_legendary")) return new[] { "Plant" };
            if (id.Contains("warlord_legendary")) return new[] { "GhostOnKill" };
            if (id.Contains("arcanist_void_capstone")) return new[] { "EquipmentMagazineVoid" };
            if (id.Contains("tech_void_capstone")) return new[] { "MissileVoid" };
            if (id.Contains("commander_void_capstone")) return new[] { "ElementalRingVoid" };
'''
if icon_anchor in ui:
    ui = ui.replace(icon_anchor, icon_anchor + icon_extra)

save(p, ui)

# ---------- Version/package ----------
p, plugin = rw("Plugin.cs")
plugin = plugin.replace('public const string PluginVersion = "0.4.1";', 'public const string PluginVersion = "0.5.0";')
plugin = plugin.replace('public const string PluginVersion = "0.4.0";', 'public const string PluginVersion = "0.5.0";')
save(p, plugin)

p, manifest = rw("manifest.json")
manifest = manifest.replace('"version_number": "0.4.1"', '"version_number": "0.5.0"').replace('"version_number": "0.4.0"', '"version_number": "0.5.0"')
manifest = manifest.replace('three specializations per class', 'seven classes with three specializations each')
save(p, manifest)

p, csproj = rw("PetrichorLegacy.csproj")
csproj = csproj.replace('<Version>0.4.1</Version>', '<Version>0.5.0</Version>').replace('<Version>0.4.0</Version>', '<Version>0.5.0</Version>')
save(p, csproj)

print("Applied PetrichorLegacy 0.5.0 seven-class patch")
