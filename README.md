# topsis-tactical-ai

Метод вибору тактичної стратегії (атака / оборона / відступ) агентами ігрового штучного інтелекту із застосуванням TOPSIS.

> Пендига В. В., Волкова Н. П. Метод вибору тактичної стратегії агентами ігрового штучного інтелекту із застосуванням TOPSIS. *Інформатика. Культура. Техніка*. 2026. Т. 3, № 2(4). DOI: 10.15276/ict.03.2026.08

## Структура репозиторію

```
topsis-tactical-ai/
├── TacticalAI-Unity/          Unity-проєкт (прототип)
│   ├── Assets/
│   │   ├── Scripts/           ← реалізація методу (C#) + EditMode-тести
│   │   │   ├── Core/          метод: стан агента, функції придатності, TOPSIS, вибір стратегії
│   │   │   ├── Agents/        компоненти агента (сенсор, «мозок», дії)
│   │   │   ├── Environment/   укриття, бази команд
│   │   │   └── Tests/EditMode/
│   │   ├── Scenes/  Prefabs/  Materials/  Models/  Animations/  Audio/  Textures/  Settings/   (заглушки)
│   ├── Packages/manifest.json
│   └── ProjectSettings/ProjectVersion.txt
└── simulation/                Python: симулятор бою та експерименти статті
```

## Unity-проєкт

- Версія редактора: **2022.3 LTS** (у `ProjectVersion.txt` вказано 2022.3.45f1; Unity Hub запропонує відкрити проєкт в іншій встановленій версії 2022.3).
- Відкрити: Unity Hub → **Add project from disk** → папка `TacticalAI-Unity`. Під час першого відкриття Unity створить `Library/`, `.meta`-файли та решту налаштувань.
- Тести: **Window → General → Test Runner → EditMode → Run All**. Тести звіряють C#-реалізацію з числами статті (ті самі значення дає `simulation/example_topsis.py`).
- Наразі заповнено лише `Assets/Scripts`; інші папки `Assets/` — заглушки для подальшого наповнення (сцени, префаби, моделі).

## Python-симуляція

Див. [`simulation/README.md`](simulation/README.md) — відтворення всіх таблиць і рисунка статті.

## Ліцензія

MIT — див. [`LICENSE`](LICENSE).
