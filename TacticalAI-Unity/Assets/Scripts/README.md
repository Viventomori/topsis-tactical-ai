# Assets/Scripts

| Папка | Вміст |
|---|---|
| `Core/` | Чиста реалізація методу без залежності від Unity: `AgentState` (вектор стану, формула (4)), `StrategyEvaluator` (функції придатності, табл. 2), `TopsisSolver` (формули (5)–(9), зважена сума для абляції), `TacticalDecisionMaker` (вибір i* = arg max C_i, обмеження допустимості Attack) |
| `Agents/` | MonoBehaviour-компоненти агента: `CombatAgent` (HP, боєприпаси, команда), `AgentSensor` (Allies/Enemies у радіусі R_sense), `AgentBrain` (вибір контролера та періодичне ухвалення рішень), `AgentActions` (виконання стратегій, постріли) |
| `Environment/` | `CoverZone` (тригер укриття, критерій S5), `TeamBase` (база команди, відновлення ресурсу під час Retreat) |
| `Tests/EditMode/` | NUnit-тести, що звіряють реалізацію з числами статті (табл. 4, 7, 8; підрозд. 4.5–4.6) |

Налаштування агента на сцені: GameObject з `Collider` + `Rigidbody` (isKinematic) + `CombatAgent` + `AgentSensor` + `AgentBrain` + `AgentActions`. Зони укриття та бази — GameObject з `Collider` (isTrigger) і `CoverZone` / `TeamBase`.
