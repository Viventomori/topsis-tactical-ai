namespace TacticalAI.Core
{
    /// <summary>
    /// Вектор стану агента s_i(τ) = (s_i1, …, s_i6) (розділ 1 статті).
    /// </summary>
    public readonly struct AgentState
    {
        /// <summary>s_i1 — поточний запас боєприпасів, 0…AMMO_max.</summary>
        public readonly float Ammo;
        /// <summary>s_i2 — витривалість (поточний запас здоров’я HP), 0…HP_max.</summary>
        public readonly float Hp;
        /// <summary>s_i3 = |Allies_i(τ)| — кількість союзників у радіусі виявлення.</summary>
        public readonly int Allies;
        /// <summary>s_i4 = |Enemies_i(τ)| — кількість ворогів у радіусі виявлення.</summary>
        public readonly int Enemies;
        /// <summary>s_i5 — наявність укриття (1 — в укритті, 0 — відкрита ділянка).</summary>
        public readonly bool InCover;
        /// <summary>s_i6 — потенційна загроза за формулою (4).</summary>
        public readonly float Threat;

        public AgentState(float ammo, float hp, int allies, int enemies, bool inCover)
            : this(ammo, hp, allies, enemies, inCover, ThreatLevel(allies, enemies)) { }

        public AgentState(float ammo, float hp, int allies, int enemies, bool inCover, float threat)
        {
            Ammo = ammo;
            Hp = hp;
            Allies = allies;
            Enemies = enemies;
            InCover = inCover;
            Threat = threat;
        }

        /// <summary>Формула (4): s_i6 = 10 · |Enemies| / (|Enemies| + |Allies| + 1), s_i6 ∈ [0; 10).</summary>
        public static float ThreatLevel(int allies, int enemies)
        {
            return 10f * enemies / (enemies + allies + 1);
        }

        public override string ToString()
        {
            return $"ammo={Ammo}, hp={Hp}, allies={Allies}, enemies={Enemies}, cover={InCover}, threat={Threat:0.00}";
        }
    }
}
